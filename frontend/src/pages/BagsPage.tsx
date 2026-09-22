import { useEffect, useState } from "react";
import { api } from "../api/client";
type Seg = "front" | "back";
type Bag = { id: number; route_id: number; bag_index: number; segment: Seg; weight_kg: number; volume_l: number; items: { stop_name: string; weight_kg: number; volume_l: number }[] };
const SEG_LABEL: Record<Seg, string> = { front: "前段", back: "后段" };
export default function BagsPage() {
  const [rows, setRows] = useState<Bag[]>([]);
  useEffect(() => { api<Bag[]>("/bags").then(setRows); }, []);
  return (<>
    <h2>袋明细</h2>
    <table className="table"><thead><tr><th>路线</th><th>袋号</th><th>段</th><th>重量</th><th>体积</th><th>订户</th></tr></thead>
    <tbody>{rows.map(b => <tr key={b.id}><td>{b.route_id}</td><td>{b.bag_index}</td>
      <td><span className={`seg-badge seg-badge--${b.segment}`}>{SEG_LABEL[b.segment] ?? b.segment}</span></td>
      <td className="mono">{b.weight_kg}</td><td className="mono">{b.volume_l}</td>
      <td>{b.items.map(i => i.stop_name).join(" → ")}</td></tr>)}
      {!rows.length && <tr><td colSpan={6}>尚无装袋结果，请先执行装袋</td></tr>}
    </tbody></table>
  </>);
}
