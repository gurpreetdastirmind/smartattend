export default function RosterTable({ rows, setRows }) {
  const update = (i, status) => {
    const next = [...rows];
    next[i] = { ...next[i], status };
    setRows(next);
  };
  return (
    <table width="100%" cellPadding="8" style={{ borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th align="left">Roll</th>
          <th align="left">Name</th>
          <th align="left">Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} style={{ borderTop: "1px solid #ddd" }}>
            <td>{r.roll_no || "-"}</td>
            <td>{r.full_name}</td>
            <td>
              <select value={r.status} onChange={(e) => update(i, e.target.value)}>
                <option>UNMARKED</option>
                <option>PRESENT</option>
                <option>ABSENT</option>
              </select>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}