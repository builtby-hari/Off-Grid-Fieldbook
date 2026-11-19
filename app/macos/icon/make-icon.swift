// Draws the 1024px app icon: a sun rising behind two-tone peaks on a deep green tile.
import AppKit
let px = 1024
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: px, pixelsHigh: px, bitsPerSample: 8, samplesPerPixel: 4,
                           hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
func c(_ r: Double, _ g: Double, _ b: Double) -> NSColor { NSColor(red: r/255, green: g/255, blue: b/255, alpha: 1) }
let tile = NSBezierPath(roundedRect: NSRect(x: 100, y: 100, width: 824, height: 824), xRadius: 185, yRadius: 185)
tile.addClip()
NSGradient(starting: c(38, 84, 52), ending: c(14, 34, 22))!.draw(in: tile, angle: -90)
// sun with a soft glow
NSGradient(starting: c(255, 214, 120).withAlphaComponent(0.35), ending: c(255, 214, 120).withAlphaComponent(0))!
  .draw(in: NSBezierPath(ovalIn: NSRect(x: 300, y: 330, width: 430, height: 430)), relativeCenterPosition: .zero)
c(250, 200, 95).setFill(); NSBezierPath(ovalIn: NSRect(x: 395, y: 425, width: 240, height: 240)).fill()
// back peak
let back = NSBezierPath()
back.move(to: NSPoint(x: 430, y: 300)); back.line(to: NSPoint(x: 690, y: 600)); back.line(to: NSPoint(x: 960, y: 300)); back.close()
c(170, 196, 176).setFill(); back.fill()
// front peak with snow cap
let front = NSBezierPath()
front.move(to: NSPoint(x: 60, y: 300)); front.line(to: NSPoint(x: 400, y: 690)); front.line(to: NSPoint(x: 740, y: 300)); front.close()
c(244, 246, 242).setFill(); front.fill()
let shade = NSBezierPath()
shade.move(to: NSPoint(x: 400, y: 690)); shade.line(to: NSPoint(x: 740, y: 300)); shade.line(to: NSPoint(x: 470, y: 300)); shade.close()
c(214, 222, 214).setFill(); shade.fill()
// ground
c(20, 46, 30).setFill(); NSBezierPath(rect: NSRect(x: 0, y: 0, width: 1024, height: 300)).fill()
c(250, 200, 95).withAlphaComponent(0.9).setFill(); NSBezierPath(rect: NSRect(x: 0, y: 296, width: 1024, height: 8)).fill()
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
