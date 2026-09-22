import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
type Seg = "front" | "back";
type S = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number; segment: Seg };
type R = { id: number; name: string };
const SEG_LABEL: Record<Seg, string> = { front: "前段", back: "后段" };
export default function StopsPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [seg, setSeg] = useState<"" | Seg>("");
  const [rows, setRows] = useState<S[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  const load = useCallback(() => {
    if (rid === "") return;
    api<S[]>(`/stops?route_id=${rid}${seg ? `&segment=${seg}` : ""}`).then(setRows);
  }, [rid, seg]);
  useEffect(load, [load]);
  async function setSegment(s: S, segment: Seg) {
    setErr("");
    try {
      await api<S>(`/stops/${s.id}`, { method: "PATCH", body: JSON.stringify({ segment }) });
      load();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>订户点</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <div className="seg-filter">
        {([["", "全部"], ["front", "前段"], ["back", "后段"]] as const).map(([v, label]) => (
          <button key={v} className={seg === v ? "on" : ""} onClick={() => setSeg(v)}>{label}</button>
        ))}
      </div>
    </div>
    {err && <div className="err">{err}</div>}
    <div className="route-strip">
      {rows.map(s => (
        <div className="stop-chip" key={s.id}>
          <span className="seq">#{s.seq}</span>
          <strong>{s.name}</strong>
          <span className="mono">{s.weight_kg}kg · {s.volume_l}L</span>
          <span className={`seg-badge seg-badge--${s.segment}`}>{SEG_LABEL[s.segment]}</span>
          <button className="seg-toggle" onClick={() => setSegment(s, s.segment === "front" ? "back" : "front")}>
            改为{s.segment === "front" ? "后段" : "前段"}
          </button>
        </div>
      ))}
      {!rows.length && <span className="stop-timeline-empty">该筛选下暂无订户点</span>}
    </div>
  </>);
}
