/**
 * Energy formatting utility with E/mE unit system
 *
 * E = base energy unit (dimensionless)
 * mE = milli-E = 0.001 E
 */

/**
 * Format energy value with automatic E/mE unit switching
 * Switches to mE when value would display as 0.00... with given decimals
 *
 * @param value - Energy value in E units
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string like "0.10 E" or "23.9 mE"
 */
export function formatEnergy(value: number | undefined | null, decimals: number = 2): string {
  if (value === undefined || value === null) return '-';

  const threshold = Math.pow(10, -decimals);
  if (value > 0 && value < threshold) {
    // Use mE (milli-E)
    return (value * 1000).toFixed(decimals) + ' mE';
  }
  return value.toFixed(decimals) + ' E';
}

/**
 * Determine if mE unit should be used for a given max energy value
 * Used for matrix displays where we want consistent units across all cells
 *
 * @param maxEnergy - Maximum energy value in the dataset
 * @param decimals - Number of decimal places used for display
 * @returns true if mE should be used
 */
export function shouldUseMilliE(maxEnergy: number, decimals: number = 2): boolean {
  const threshold = Math.pow(10, -decimals);
  return maxEnergy > 0 && maxEnergy < threshold;
}

/**
 * Get the appropriate energy unit label
 * @param useMilliE - Whether to use mE units
 * @returns "E" or "mE"
 */
export function getEnergyUnit(useMilliE: boolean): string {
  return useMilliE ? 'mE' : 'E';
}

/**
 * Scale energy value based on unit selection
 * @param value - Energy value in E units
 * @param useMilliE - Whether to scale to mE
 * @returns Scaled value
 */
export function scaleEnergy(value: number, useMilliE: boolean): number {
  return useMilliE ? value * 1000 : value;
}
