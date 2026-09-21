import {test} from 'node:test';
import assert from 'node:assert/strict';
import {calculateScenario} from '../src/lib/scenario.ts';
import {allocateHeuristic} from '../src/lib/allocation.ts';
const baseline={baselineTouristsK:1,baselineExcursionistsK:1,baselineAlos:2,baselineSpendPerNight:100,accomVAI:0.8,guestsPerRoom:2,residentHouseholds:null,hasCapacityData:true,totalRooms:100,baselineAor:50,affectedShare:0,deltaAlos:0,conversionRate:0,vfrConversionRate:0,yieldUplift:0,unpaidVfrInput:100};
test('zero policy yields zero benefit',()=>assert.equal(calculateScenario(baseline).totalAdditionalAccomSpendMil,0));
test('VFR existing nights are transferred, not new tourist nights',()=>{
 const r=calculateScenario({...baseline,affectedShare:100,deltaAlos:1,vfrConversionRate:100});
 assert.equal(r.additionalTouristNightsK,1); assert.equal(r.transferredExistingNightsK,2);
 assert.equal(r.totalAdditionalGuestNightsK,3); assert.equal(r.totalAdditionalAccomSpendMil,0.255);
});
test('missing capacity stays unknown',()=>assert.equal(calculateScenario({...baseline,hasCapacityData:false,totalRooms:null}).simulatedAor,null));
const candidate=(id:string,cost:number,value:number)=>({corridor_id:id,destination:'D',eligible:true,cost_rm_million:cost,expected_gva_rm_million:value,p10_gva_rm_million:value/2,risk_adjusted_gva_rm_million:value*0.8,daily_rooms_demanded:1,additional_spend_rm_million:value,additional_nights:10});
test('allocation has eligibility and budget constraints',()=>{
 const r=allocateHeuristic([candidate('A',1,10),{...candidate('B',0,100),eligible:false}],{D:{hotel_rooms:100,aor:50}},1,80,{},'expected');
 assert.equal(r.displayCorridors.length,1); assert.equal(r.summary.total_cost_rm_million,1);
 assert.equal(allocateHeuristic([candidate('A',1,10)],{},1,80,{},'expected').displayCorridors.length,0);
});
test('greedy can be suboptimal; never advertise optimality',()=>{
 const r=allocateHeuristic([candidate('A',3,5),candidate('B',2,3),candidate('C',2,3)],{D:{hotel_rooms:100,aor:50}},4,80,{},'expected');
 assert.equal(r.summary.total_expected_gva_rm_million,5); assert.ok(r.summary.total_expected_gva_rm_million < 6); assert.match(r.summary.method,/optimality not established/);
});
test('cost overrides and risk mode affect allocation',()=>{
 const candidates=[candidate('A',1,10),{...candidate('B',1,9),p10_gva_rm_million:8}]; const b={D:{hotel_rooms:100,aor:50}};
 assert.equal(allocateHeuristic(candidates,b,1,80,{},'expected').displayCorridors[0].corridor_id,'A');
 assert.equal(allocateHeuristic(candidates,b,1,80,{},'conservative_p10').displayCorridors[0].corridor_id,'B');
 assert.equal(allocateHeuristic(candidates,b,1,80,{A:2000},'expected').displayCorridors[0].corridor_id,'B');
});
