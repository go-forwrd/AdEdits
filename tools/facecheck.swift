// Score frames for usable faces with Apple Vision (on-device). For each image prints one TSV line:
// path, face count, largest face x y w h (normalised, origin bottom-left), left/right eye openness,
// yaw, capture quality. Eye openness = eye contour height / width (blink ~< 0.15).
// Usage: swift tools/facecheck.swift <img> [<img> ...]
import CoreImage
import Foundation
import Vision

func openness(_ r: VNFaceLandmarkRegion2D?) -> Double {
    guard let pts = r?.normalizedPoints, pts.count > 2 else { return -1 }
    let xs = pts.map { Double($0.x) }, ys = pts.map { Double($0.y) }
    let w = (xs.max()! - xs.min()!), h = (ys.max()! - ys.min()!)
    return w > 0 ? h / w : -1
}

for path in CommandLine.arguments.dropFirst() {
    guard let ci = CIImage(contentsOf: URL(fileURLWithPath: path)) else { continue }
    let lm = VNDetectFaceLandmarksRequest()
    let q = VNDetectFaceCaptureQualityRequest()
    let h = VNImageRequestHandler(ciImage: ci)
    try? h.perform([lm, q])
    let faces = lm.results ?? []
    guard let f = faces.max(by: { $0.boundingBox.width < $1.boundingBox.width }) else {
        print("\(path)\t0"); continue
    }
    let b = f.boundingBox
    let qual = (q.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width })?.faceCaptureQuality ?? -1
    let yaw = f.yaw?.doubleValue ?? 0
    print(String(format: "%@\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.2f\t%.3f", path, faces.count,
                 b.minX, b.minY, b.width, b.height,
                 openness(f.landmarks?.leftEye), openness(f.landmarks?.rightEye), yaw, qual))
}
