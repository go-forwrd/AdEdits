// On-device subject cutout with Apple Vision (the "Lift subject" engine in Photos). Free, local.
// Usage: swift tools/liftsubject.swift <in.jpg|png> <out.png> [instance indices, e.g. 1,2]
// Without indices every detected foreground instance is kept. Prints the instance count.
import AppKit
import CoreImage
import Foundation
import Vision

let args = CommandLine.arguments
guard args.count >= 3 else {
    print("usage: liftsubject <in> <out.png> [indices]")
    exit(2)
}
let url = URL(fileURLWithPath: args[1])
guard let ci = CIImage(contentsOf: url) else { print("cannot read \(args[1])"); exit(1) }
let req = VNGenerateForegroundInstanceMaskRequest()
let handler = VNImageRequestHandler(ciImage: ci)
try handler.perform([req])
guard let obs = req.results?.first else { print("no subject found"); exit(1) }
print("instances: \(obs.allInstances.count)")
var keep = obs.allInstances
if args.count >= 4 {
    keep = IndexSet(args[3].split(separator: ",").compactMap { Int($0) })
}
let buf = try obs.generateMaskedImage(ofInstances: keep, from: handler, croppedToInstancesExtent: false)
let out = CIImage(cvPixelBuffer: buf)
let ctx = CIContext()
guard let cs = CGColorSpace(name: CGColorSpace.sRGB) else { exit(1) }
try ctx.writePNGRepresentation(of: out, to: URL(fileURLWithPath: args[2]), format: .RGBA8, colorSpace: cs)
print("wrote \(args[2])")
