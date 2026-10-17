export const REQUIRED_FIELD_MESSAGE = 'This field is required.'

export const getRequiredTextError = (value: string, maxLength: number): string | null => {
  const trimmedValue = value.trim()
  if (trimmedValue.length === 0) {
    return REQUIRED_FIELD_MESSAGE
  }
  if (trimmedValue.length > maxLength) {
    return `Must be at most ${maxLength} characters.`
  }
  return null
}

export const getSelectionError = (value: string | null): string | null => {
  if (value === null || value.trim().length === 0) {
    return REQUIRED_FIELD_MESSAGE
  }
  return null
}

export const getWholeNumberRangeError = (
  value: string,
  minValue: number,
  maxValue: number,
): string | null => {
  const trimmedValue = value.trim()
  if (trimmedValue.length === 0) {
    return REQUIRED_FIELD_MESSAGE
  }
  const numericValue = Number(trimmedValue)
  if (!Number.isInteger(numericValue) || numericValue < minValue || numericValue > maxValue) {
    return `Must be a whole number from ${minValue} to ${maxValue}.`
  }
  return null
}
