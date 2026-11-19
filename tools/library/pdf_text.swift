// pdf_text: write the text of each PDF page as JSON.
// Usage: pdf_text <pdf> <out.json>
// Output: a JSON array, one object per page: {"p": 1-based page number, "x": page text}.
// Whitespace runs are collapsed to single spaces. Only parses the file: no network, nothing is run.
// Build: swiftc -O tools/library/pdf_text.swift -o tools/library/pdf_text

import Foundation
import PDFKit

func collapse(_ s: String) -> String {
    var out = ""
    out.reserveCapacity(s.count)
    var inSpace = false
    for ch in s.unicodeScalars {
        if CharacterSet.whitespacesAndNewlines.contains(ch) {
            if !inSpace && !out.isEmpty { out.append(" ") }
            inSpace = true
        } else {
            out.unicodeScalars.append(ch)
            inSpace = false
        }
    }
    while out.hasSuffix(" ") { out.removeLast() }
    return out
}

let args = CommandLine.arguments
guard args.count == 3 else {
    FileHandle.standardError.write("usage: pdf_text <pdf> <out.json>\n".data(using: .utf8)!)
    exit(2)
}

let url = URL(fileURLWithPath: args[1])
guard let doc = PDFDocument(url: url) else {
    FileHandle.standardError.write("pdf_text: cannot open \(args[1])\n".data(using: .utf8)!)
    exit(1)
}

struct Page: Encodable {
    let p: Int
    let x: String
}

var pages: [Page] = []
pages.reserveCapacity(doc.pageCount)
for i in 0..<doc.pageCount {
    let text = doc.page(at: i)?.string ?? ""
    pages.append(Page(p: i + 1, x: collapse(text)))
}

do {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.withoutEscapingSlashes]
    let data = try encoder.encode(pages)
    try data.write(to: URL(fileURLWithPath: args[2]), options: .atomic)
} catch {
    FileHandle.standardError.write("pdf_text: cannot write \(args[2]): \(error)\n".data(using: .utf8)!)
    exit(1)
}
print(doc.pageCount)
