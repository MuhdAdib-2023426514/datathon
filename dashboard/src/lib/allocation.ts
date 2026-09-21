export function allocateHeuristic(candidates: any[], baselines: Record<string, any>, budget: number, threshold: number, costs: Record<string, number>, mode: string) {
  if (!Number.isFinite(budget) || budget < 0 || !Number.isFinite(threshold) || threshold <= 0 || threshold > 100) throw new Error('Invalid budget or threshold');
  const field = mode === 'conservative_p10' ? 'p10_gva_rm_million' : mode === 'risk_adjusted' ? 'risk_adjusted_gva_rm_million' : 'expected_gva_rm_million';
  const pool = candidates.filter(c => c.eligible === true).map(c => ({...c, cost_rm_million: costs[c.corridor_id] === undefined ? c.cost_rm_million : costs[c.corridor_id]/1000})).filter(c => Number.isFinite(c.cost_rm_million) && c.cost_rm_million > 0 && Number.isFinite(c[field]) && Number.isFinite(c.daily_rooms_demanded) && c.daily_rooms_demanded >= 0);
  pool.sort((a,b) => b[field]/b.cost_rm_million-a[field]/a.cost_rm_million);
  const rooms: Record<string, number> = {}, counts: Record<string,number> = {};
  const selected: any[]=[]; let cost=0;
  for (const c of pool) {
    const b=baselines[c.destination];
    if (!b || !Number.isFinite(b.hotel_rooms) || b.hotel_rooms <= 0 || !Number.isFinite(b.aor) || b.aor < 0 || b.aor > 100) continue;
    const headroom=Math.max(0,b.hotel_rooms*(threshold-b.aor)/100);
    if (cost+c.cost_rm_million > budget+1e-9 || (counts[c.destination]??0)>=4 || (rooms[c.destination]??0)+c.daily_rooms_demanded > headroom+1e-9) continue;
    selected.push(c); cost+=c.cost_rm_million; counts[c.destination]=(counts[c.destination]??0)+1; rooms[c.destination]=(rooms[c.destination]??0)+c.daily_rooms_demanded;
  }
  const sum=(field:string)=>selected.reduce((v,c)=>v+c[field],0);
  const gva=sum('expected_gva_rm_million');
  return {displayCorridors:selected,isCustomSolution:true,summary:{
    method:'greedy heuristic; optimality not established', budget_allocated_rm_million:budget,
    total_cost_rm_million:cost,budget_utilization_pct:budget?cost/budget*100:0,
    total_expected_gva_rm_million:gva,total_p10_gva_rm_million:sum('p10_gva_rm_million'),
    total_risk_adjusted_gva_rm_million:sum('risk_adjusted_gva_rm_million'),
    total_additional_spend_rm_million:sum('additional_spend_rm_million'),total_additional_nights:sum('additional_nights'),
    objective_mode:mode,value_to_cost_multiple:cost>0?gva/cost:0,portfolio_roi_multiplier:cost>0?gva/cost:0,total_corridors_funded:selected.length,
    planning_threshold_pct:threshold,cost_status:'Illustrative cost assumptions or user-supplied costs',
  }};
}
