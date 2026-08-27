import { ImageResponse } from "next/og";
import { site } from "@/content/site";

export const alt = `${site.name} — ${site.role}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 80,
          background: "#000",
          color: "#f5f5f7",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            width: 520,
            height: 520,
            borderRadius: 999,
            background: "rgba(41, 151, 255, 0.22)",
            filter: "blur(8px)",
            top: -80,
            left: -40,
          }}
        />
        <div style={{ fontSize: 22, color: "#86868b", letterSpacing: "0.12em" }}>
          {site.role.toUpperCase()}
        </div>
        <div
          style={{
            marginTop: 18,
            fontSize: 84,
            fontWeight: 600,
            letterSpacing: "-0.04em",
            lineHeight: 1.02,
          }}
        >
          {site.name}
        </div>
        <div
          style={{
            marginTop: 28,
            maxWidth: 860,
            fontSize: 32,
            color: "#a1a1a6",
            lineHeight: 1.25,
          }}
        >
          {site.tagline}
        </div>
      </div>
    ),
    { ...size },
  );
}
