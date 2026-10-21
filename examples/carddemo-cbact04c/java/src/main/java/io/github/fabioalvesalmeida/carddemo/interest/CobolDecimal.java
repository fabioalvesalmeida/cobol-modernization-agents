package io.github.fabioalvesalmeida.carddemo.interest;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Reproduces how a COBOL receiving field stores a numeric result.
 *
 * <p>A {@code COMPUTE} without {@code ROUNDED} truncates extra decimals toward zero, and without
 * {@code ON SIZE ERROR} it silently drops high-order integer digits that do not fit the PIC.
 * Business rule cards record both behaviors; this class is the single place they are implemented.
 */
public final class CobolDecimal {

    private CobolDecimal() {}

    /**
     * Store {@code value} into a signed field {@code S9(integerDigits)V9(scale)}.
     *
     * @param value         exact result of the arithmetic expression
     * @param integerDigits digits before the implied decimal point
     * @param scale         digits after the implied decimal point
     */
    public static BigDecimal store(BigDecimal value, int integerDigits, int scale) {
        BigDecimal truncated = value.setScale(scale, RoundingMode.DOWN);
        BigDecimal modulus = BigDecimal.TEN.pow(integerDigits);
        BigDecimal integerPart = truncated.setScale(0, RoundingMode.DOWN);
        BigDecimal fraction = truncated.subtract(integerPart);
        BigDecimal keptInteger = integerPart.remainder(modulus); // keeps the sign, like COBOL
        return keptInteger.add(fraction).setScale(scale, RoundingMode.UNNECESSARY);
    }
}
