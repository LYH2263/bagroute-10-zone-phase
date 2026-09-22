import { useEffect, useState } from "react";
import { api } from "../api/client";
type S = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number; segment: string };
type R = { id: number; name: string };
type SegFilter = "" | "front" | "rear";
const segLabel = (s: string) => (s === "rear" ? "后段" : "前段");
export default function StopsPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [seg, setSeg] = useState<SegFilter>("");
  const [rows, setRows] = useState<S[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  useEffect(() => {
    if (rid === "") return;
    const q = seg ? `&segment=${seg}` : "";
    api<S[]>(`/stops?route_id=${rid}${q}`).then(setRows).catch(() => setRows([]));
  }, [rid, seg]);
  async function toggle(s: S) {
    setErr("");
    const next = s.segment === "rear" ? "front" : "rear";
    try {
      const updated = await api<S>(`/stops/${s.id}`, {
        method: "PATCH",
        body: JSON.stringify({ segment: next }),
      });
      setRows(rs => (seg && updated.segment !== seg ? rs.filter(x => x.id !== s.id) : rs.map(x => (x.id === s.id ? updated : x))));
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>订户点</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <div className="seg-filter" role="group" aria-label="段别筛选">
        {(["", "front", "rear"] as SegFilter[]).map(v => (
          <button key={v || "all"}
            className={seg === v ? "seg-btn seg-btn--on" : "seg-btn"}
            onClick={() => setSeg(v)}>
            {v === "" ? "全部" : segLabel(v)}
          </button>
        ))}
      </div>
    </div>
    {err && <div className="err">{err}</div>}
    <div className="route-strip">
      {rows.map(s => (
        <div className={`stop-chip stop-chip--${s.segment}`} key={s.id}>
          <span className="seq">#{s.seq}</span>
          <strong>{s.name}</strong>
          <span className="mono">{s.weight_kg}kg · {s.volume_l}L</span>
          <button className="seg-toggle" title="切换前/后段" onClick={() => toggle(s)}>
            <span className={`seg-badge seg-badge--${s.segment}`}>{segLabel(s.segment)}</span>
            改为{s.segment === "rear" ? "前段" : "后段"}
          </button>
        </div>
      ))}
      {!rows.length && <div className="meter-empty">该筛选下暂无站点</div>}
    </div>
  </>);
}
