// pdf_extract: per-page text lines with font size and bold flag (PDFKit),
// figure and table flags, and PNG renders of flagged pages (CoreGraphics / ImageIO).
// Usage: pdf_extract <pdf> <outdir>
// Writes <outdir>/pages.json and <outdir>/img/page-NNN.png for flagged pages.
// Reads only. The PDF is parsed, never executed.

import Foundation
import AppKit
import PDFKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
if args.count != 3 {
    FileHandle.standardError.write("usage: pdf_extract <pdf> <outdir>\n".data(using: .utf8)!)
    exit(2)
}
let pdfPath = args[1]
let outDir = args[2]
let fm = FileManager.default
let imgDir = (outDir as NSString).appendingPathComponent("img")
try? fm.createDirectory(atPath: imgDir, withIntermediateDirectories: true)

let pdfURL = URL(fileURLWithPath: pdfPath)
guard let doc = PDFDocument(url: pdfURL) else {
    FileHandle.standardError.write("cannot open PDF: \(pdfPath)\n".data(using: .utf8)!)
    exit(1)
}
guard let cgDoc = CGPDFDocument(pdfURL as CFURL) else {
    FileHandle.standardError.write("cannot open PDF with CoreGraphics\n".data(using: .utf8)!)
    exit(1)
}

// MARK: - Figure detection on CGPDFPage

func imageSizeOK(_ dict: CGPDFDictionaryRef) -> Bool {
    var w: CGPDFInteger = 0
    var h: CGPDFInteger = 0
    let okW = CGPDFDictionaryGetInteger(dict, "Width", &w)
    let okH = CGPDFDictionaryGetInteger(dict, "Height", &h)
    return okW && okH && w >= 120 && h >= 120
}

// Count qualifying images in an XObject dictionary; looks one level into Form XObjects.
func countBigImages(_ xobjects: CGPDFDictionaryRef, depth: Int) -> Int {
    var count = 0
    CGPDFDictionaryApplyBlock(xobjects, { _, value, _ in
        var stream: CGPDFStreamRef? = nil
        guard CGPDFObjectGetValue(value, .stream, &stream), let s = stream,
              let sdict = CGPDFStreamGetDictionary(s) else { return true }
        var subtype: UnsafePointer<CChar>? = nil
        guard CGPDFDictionaryGetName(sdict, "Subtype", &subtype), let st = subtype else { return true }
        let name = String(cString: st)
        if name == "Image" {
            if imageSizeOK(sdict) { count += 1 }
        } else if name == "Form" && depth < 1 {
            var res: CGPDFDictionaryRef? = nil
            if CGPDFDictionaryGetDictionary(sdict, "Resources", &res), let r = res {
                var xo: CGPDFDictionaryRef? = nil
                if CGPDFDictionaryGetDictionary(r, "XObject", &xo), let x = xo {
                    count += countBigImages(x, depth: depth + 1)
                }
            }
        }
        return true
    }, nil)
    return count
}

func pageImageCount(_ index: Int) -> Int {
    guard let cgPage = cgDoc.page(at: index + 1) else { return 0 }
    guard let pdict = cgPage.dictionary else { return 0 }
    var res: CGPDFDictionaryRef? = nil
    guard CGPDFDictionaryGetDictionary(pdict, "Resources", &res), let r = res else { return 0 }
    var xo: CGPDFDictionaryRef? = nil
    guard CGPDFDictionaryGetDictionary(r, "XObject", &xo), let x = xo else { return 0 }
    return countBigImages(x, depth: 0)
}


// MARK: - Vector artwork (path operators in the content stream)

nonisolated(unsafe) var vecCurves = 0
nonisolated(unsafe) var vecLines = 0

let vecCurveCallback: @convention(c) (CGPDFScannerRef, UnsafeMutableRawPointer?) -> Void = { _, _ in vecCurves += 1 }
let vecLineCallback: @convention(c) (CGPDFScannerRef, UnsafeMutableRawPointer?) -> Void = { _, _ in vecLines += 1 }

// Returns (curve segments, line segments) painted by the page content stream.
func vectorCounts(_ index: Int) -> (Int, Int) {
    guard let cgPage = cgDoc.page(at: index + 1) else { return (0, 0) }
    vecCurves = 0
    vecLines = 0
    guard let table = CGPDFOperatorTableCreate() else { return (0, 0) }
    CGPDFOperatorTableSetCallback(table, "c", vecCurveCallback)
    CGPDFOperatorTableSetCallback(table, "v", vecCurveCallback)
    CGPDFOperatorTableSetCallback(table, "y", vecCurveCallback)
    CGPDFOperatorTableSetCallback(table, "l", vecLineCallback)
    let cs = CGPDFContentStreamCreateWithPage(cgPage)
    let scanner = CGPDFScannerCreate(cs, table, nil)
    _ = CGPDFScannerScan(scanner)
    // Also scan Form XObjects one level down, where many designed graphics live.
    if let pdict = cgPage.dictionary {
        var res: CGPDFDictionaryRef? = nil
        if CGPDFDictionaryGetDictionary(pdict, "Resources", &res), let r = res {
            var xo: CGPDFDictionaryRef? = nil
            if CGPDFDictionaryGetDictionary(r, "XObject", &xo), let x = xo {
                CGPDFDictionaryApplyBlock(x, { _, value, _ in
                    var stream: CGPDFStreamRef? = nil
                    guard CGPDFObjectGetValue(value, .stream, &stream), let st = stream,
                          let sdict = CGPDFStreamGetDictionary(st) else { return true }
                    var subtype: UnsafePointer<CChar>? = nil
                    guard CGPDFDictionaryGetName(sdict, "Subtype", &subtype), let stp = subtype,
                          String(cString: stp) == "Form" else { return true }
                    var fres: CGPDFDictionaryRef? = nil
                    _ = CGPDFDictionaryGetDictionary(sdict, "Resources", &fres)
                    let fcs = CGPDFContentStreamCreateWithStream(st, fres ?? r, cs)
                    let fsc = CGPDFScannerCreate(fcs, table, nil)
                    _ = CGPDFScannerScan(fsc)
                    return true
                }, nil)
            }
        }
    }
    return (vecCurves, vecLines)
}

// MARK: - Line extraction

struct Line {
    var text: String
    var size: Double
    var bold: Bool
    var font: String
    var x0: Double, y0: Double, x1: Double, y1: Double
    var hasBounds: Bool
    var leadBold: String
}

func isBoldFont(_ font: NSFont?) -> Bool {
    guard let f = font else { return false }
    let n = f.fontName.lowercased()
    if n.contains("bold") || n.contains("black") || n.contains("heavy") || n.contains("semibold") {
        return true
    }
    return f.fontDescriptor.symbolicTraits.contains(.bold)
}

// Replacement char handling happens in Python; here we only keep raw text.
func lineFromSelection(_ sel: PDFSelection, page: PDFPage) -> Line? {
    let raw = sel.string ?? ""
    let text = raw.replacingOccurrences(of: "\r", with: " ").replacingOccurrences(of: "\n", with: " ")
    if text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { return nil }

    var sizeChars: [Double: Int] = [:]
    var boldChars = 0
    var totalChars = 0
    var fontName = ""
    var leadBold = ""
    var leadDone = false
    if let attr = sel.attributedString {
        let ns = attr.string as NSString
        attr.enumerateAttribute(.font, in: NSRange(location: 0, length: attr.length), options: []) { value, range, _ in
            let font = value as? NSFont
            let size = font.map { (Double($0.pointSize) * 10).rounded() / 10 } ?? 0
            sizeChars[size, default: 0] += range.length
            totalChars += range.length
            let bold = isBoldFont(font)
            if bold { boldChars += range.length }
            if fontName.isEmpty, let f = font { fontName = f.fontName }
            // Leading bold run (a run-in heading), only while it is still the start of the line.
            if !leadDone {
                if bold && range.location == leadBold.utf16.count {
                    leadBold += ns.substring(with: range)
                } else {
                    leadDone = true
                }
            }
        }
    }
    var dominant = 0.0
    var best = -1
    for (s, c) in sizeChars where c > best || (c == best && s > dominant) {
        best = c
        dominant = s
    }
    let bold = totalChars > 0 && Double(boldChars) / Double(totalChars) >= 0.8

    let b = sel.bounds(for: page)
    let hasBounds = b.size.width > 0 || b.size.height > 0
    return Line(
        text: text,
        size: dominant,
        bold: bold,
        font: fontName,
        x0: Double(b.minX), y0: Double(b.minY), x1: Double(b.maxX), y1: Double(b.maxY),
        hasBounds: hasBounds,
        leadBold: leadBold
    )
}

// MARK: - Table heuristic

func looksLikeTable(_ lines: [Line]) -> (Bool, [String]) {
    var reasons: [String] = []
    let shortDigit = lines.filter { $0.text.count < 40 && $0.text.rangeOfCharacter(from: .decimalDigits) != nil }
    if shortDigit.count >= 8 {
        reasons.append("short digit lines: \(shortDigit.count)")
    }
    let withBounds = lines.filter { $0.hasBounds }
    // Columns count only when their lines carry digits (plain multi-column prose is not a table).
    var buckets: [Int: Int] = [:]
    var digitBuckets: [Int: Int] = [:]
    for l in withBounds {
        let key = Int((l.x0 / 4).rounded())
        buckets[key, default: 0] += 1
        if l.text.rangeOfCharacter(from: .decimalDigits) != nil { digitBuckets[key, default: 0] += 1 }
    }
    let columns = buckets.filter { $0.value >= 3 && (digitBuckets[$0.key] ?? 0) * 3 >= $0.value }.count
    if columns >= 3 {
        reasons.append("left-edge columns of digit lines shared by 3+ lines: \(columns)")
    }
    return (!reasons.isEmpty, reasons)
}

// MARK: - Render

func renderPage(_ page: PDFPage, to path: String) -> Bool {
    let box = page.bounds(for: .mediaBox)
    let dpi: CGFloat = 110
    let scale = dpi / 72.0
    let wpx = Int((box.width * scale).rounded())
    let hpx = Int((box.height * scale).rounded())
    guard wpx > 0, hpx > 0 else { return false }
    let cs = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: nil, width: wpx, height: hpx, bitsPerComponent: 8,
                              bytesPerRow: 0, space: cs,
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: wpx, height: hpx))
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -box.minX, y: -box.minY)
    page.draw(with: .mediaBox, to: ctx)
    guard let image = ctx.makeImage() else { return false }
    let url = URL(fileURLWithPath: path) as CFURL
    guard let dest = CGImageDestinationCreateWithURL(url, UTType.png.identifier as CFString, 1, nil) else { return false }
    CGImageDestinationAddImage(dest, image, nil)
    return CGImageDestinationFinalize(dest)
}

// MARK: - Main loop

var pagesOut: [[String: Any]] = []
let pageCount = doc.pageCount
for i in 0..<pageCount {
    guard let page = doc.page(at: i) else { continue }
    let mediaBox = page.bounds(for: .mediaBox)

    var lines: [Line] = []
    if let whole = page.selection(for: mediaBox) {
        for sel in whole.selectionsByLine() {
            if let l = lineFromSelection(sel, page: page) { lines.append(l) }
        }
    }
    let chars = lines.reduce(0) { $0 + $1.text.count }

    let imgCount = pageImageCount(i)
    let (curves, linesN) = vectorCounts(i)
    var figureReasons: [String] = []
    if imgCount > 0 { figureReasons.append("large image XObjects: \(imgCount)") }
    if curves >= 24 { figureReasons.append("vector artwork: \(curves) curve segments") }
    if chars < 400 { figureReasons.append("under 400 characters of text (\(chars))") }
    let hasFigure = !figureReasons.isEmpty

    let (tableFlag, tableReasons) = looksLikeTable(lines)

    let pageNo = i + 1
    let num = String(format: "%03d", pageNo)
    var rendered: String? = nil
    if hasFigure || tableFlag {
        let png = (imgDir as NSString).appendingPathComponent("page-\(num).png")
        if renderPage(page, to: png) {
            rendered = "img/page-\(num).png"
        }
    }

    let lineDicts: [[String: Any]] = lines.map { l in
        [
            "text": l.text,
            "size": l.size,
            "bold": l.bold,
            "font": l.font,
            "x0": l.x0, "y0": l.y0, "x1": l.x1, "y1": l.y1,
            "bounds": l.hasBounds,
            "lead_bold": l.leadBold
        ]
    }

    pagesOut.append([
        "page": pageNo,
        "width": Double(mediaBox.width),
        "height": Double(mediaBox.height),
        "rotation": page.rotation,
        "chars": chars,
        "curve_segments": curves,
        "line_segments": linesN,
        "has_figure": hasFigure,
        "figure_reasons": figureReasons,
        "looks_like_table": tableFlag,
        "table_reasons": tableReasons,
        "rendered": rendered.map { $0 as Any } ?? NSNull(),
        "lines": lineDicts
    ])
}

let out: [String: Any] = [
    "source": pdfPath,
    "page_count": pageCount,
    "pages": pagesOut
]
let data = try JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted, .sortedKeys])
try data.write(to: URL(fileURLWithPath: (outDir as NSString).appendingPathComponent("pages.json")))
print("pages: \(pageCount)")
