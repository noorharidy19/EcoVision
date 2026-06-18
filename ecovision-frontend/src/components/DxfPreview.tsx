import { useEffect, useRef } from "react";
import { DxfViewer } from "dxf-viewer";

interface Props {
  file: File;
}

const DxfPreview = ({ file }: Props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous instance
    if (viewerRef.current) {
      viewerRef.current.Destroy();
      viewerRef.current = null;
    }

    const viewer = new DxfViewer(containerRef.current, {
      autoResize: true,
      colorCorrection: true,
      blackWhiteInversion: true,
    });

    viewerRef.current = viewer;

    const url = URL.createObjectURL(file);

    viewer.Load({ url, fonts: [] })
      .catch((err: any) => console.error("DXF load error:", err))
      .finally(() => URL.revokeObjectURL(url));

    return () => {
      viewer.Destroy();
      viewerRef.current = null;
    };
  }, [file]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", borderRadius: "8px", overflow: "hidden" }}
    />
  );
};

export default DxfPreview;