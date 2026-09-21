export interface ScenarioInput {
 baselineTouristsK: number; baselineExcursionistsK: number; baselineAlos: number;
 baselineSpendPerNight: number; accomVAI: number; guestsPerRoom: number;
 residentHouseholds: number | null; hasCapacityData: boolean; totalRooms: number | null;
 baselineAor: number | null; affectedShare: number; deltaAlos: number; conversionRate: number;
 vfrConversionRate: number; yieldUplift: number; unpaidVfrInput: number | null;
}
export function calculateScenario(input: ScenarioInput) {
  for (const key of ['baselineTouristsK','baselineExcursionistsK','baselineAlos','baselineSpendPerNight','accomVAI','guestsPerRoom','affectedShare','deltaAlos','conversionRate','vfrConversionRate','yieldUplift'] as const) {
    if (!Number.isFinite(input[key]) || input[key] < 0) throw new Error(`Invalid scenario input: ${key}`);
  }
  if (input.guestsPerRoom <= 0 || input.accomVAI > 1 || input.affectedShare > 100 || input.conversionRate > 100 || input.vfrConversionRate > 100 || input.deltaAlos > 3) throw new Error('Scenario inputs outside supported bounds');
  if (input.vfrConversionRate > 0 && input.unpaidVfrInput == null) throw new Error('VFR baseline unavailable');
  const {baselineTouristsK, baselineExcursionistsK, baselineAlos, baselineSpendPerNight, accomVAI, guestsPerRoom, residentHouseholds, hasCapacityData, totalRooms, baselineAor, affectedShare, deltaAlos, conversionRate, vfrConversionRate, yieldUplift, unpaidVfrInput} = input;
  // Real-Time Scenario Calculations (AGENTS.md Stage F & Sprint 6 Formulas)
  // 1. Stay extension with campaign affected share (Phase 22)
  const addNightsFromAlosK = baselineTouristsK * (affectedShare / 100.0) * deltaAlos;

  // 2. Converted excursionists into overnight tourists
  const convertedTouristsK = baselineExcursionistsK * (conversionRate / 100.0);
  const addNightsFromConvertedK = convertedTouristsK * (baselineAlos + deltaAlos);

  // 3. Converted unpaid VFR stays into commercial/registered paid lodging (Phase 24)
  const hasVfrData = unpaidVfrInput != null;
  const unpaidVfrPct: number = unpaidVfrInput ?? 0;
  const vfrTouristsK = baselineTouristsK * (unpaidVfrPct / 100.0);
  const convertedVfrTouristsK = vfrTouristsK * (vfrConversionRate / 100.0);
  const vfrNightsK = convertedVfrTouristsK * (baselineAlos + (affectedShare / 100) * deltaAlos);
  const vfrOverlapNightsK = convertedVfrTouristsK * (affectedShare / 100) * deltaAlos;
  const homestayNightlyRate = Math.max(75, baselineSpendPerNight * 0.85);
  const vfrAccomSpendRM = hasVfrData ? (vfrNightsK * 1e3 * homestayNightlyRate) / 1e6 : 0.0;

  // Total additional guest nights (thousands) — Phase 24 includes VFR nights
  const totalAdditionalGuestNightsK = addNightsFromAlosK - vfrOverlapNightsK + addNightsFromConvertedK + vfrNightsK;

  // New spend per night (RM)
  const newSpendPerNight = baselineSpendPerNight * (1 + yieldUplift / 100.0);

  // Additional accommodation expenditure (RM Million)
  const existingNightsK = baselineTouristsK * baselineAlos;
  const newNightsSpendRM = ((addNightsFromAlosK - vfrOverlapNightsK + addNightsFromConvertedK) * 1e3 * newSpendPerNight) / 1e6;
  const existingNightsUpliftRM = (existingNightsK * 1e3 * (newSpendPerNight - baselineSpendPerNight)) / 1e6;
  const totalAdditionalAccomSpendMil = newNightsSpendRM + existingNightsUpliftRM + vfrAccomSpendRM;

  // Potential Additional Tourism Value Added Proxy (RM Million at official VAI)
  const potentialAdditionalTdgvaMil = totalAdditionalAccomSpendMil * accomVAI;

  // Incremental Yield per Resident Household (RM / Household)
  const yieldPerHouseholdRM = (residentHouseholds && residentHouseholds > 0)
    ? (totalAdditionalAccomSpendMil * 1e6) / (residentHouseholds * 1e3)
    : 0;

  // Capacity Feasibility: Convert Guest Nights to Room Nights (Phase 23 & 24)
  const availableRoomNightsYearK = (hasCapacityData && totalRooms && totalRooms > 0) ? (totalRooms * 365) / 1e3 : null;
  const additionalRoomNightsYearK = totalAdditionalGuestNightsK / guestsPerRoom;
  const additionalAorPct = (hasCapacityData && availableRoomNightsYearK && availableRoomNightsYearK > 0)
    ? (additionalRoomNightsYearK / availableRoomNightsYearK) * 100
    : null;
  const simulatedAor = (hasCapacityData && baselineAor != null && additionalAorPct != null)
    ? baselineAor + additionalAorPct
    : null;


  return {addNightsFromAlosK, convertedTouristsK, addNightsFromConvertedK, hasVfrData, unpaidVfrPct, vfrTouristsK, convertedVfrTouristsK, vfrNightsK, vfrOverlapNightsK, homestayNightlyRate, vfrAccomSpendRM, totalAdditionalGuestNightsK, newSpendPerNight, existingNightsK, newNightsSpendRM, existingNightsUpliftRM, totalAdditionalAccomSpendMil, potentialAdditionalTdgvaMil, yieldPerHouseholdRM, availableRoomNightsYearK, additionalRoomNightsYearK, additionalAorPct, simulatedAor, additionalTouristNightsK: addNightsFromAlosK + addNightsFromConvertedK, transferredExistingNightsK: convertedVfrTouristsK * baselineAlos};
}
