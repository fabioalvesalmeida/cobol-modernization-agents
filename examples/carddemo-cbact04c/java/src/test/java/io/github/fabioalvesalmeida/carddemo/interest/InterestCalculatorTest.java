package io.github.fabioalvesalmeida.carddemo.interest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import io.github.fabioalvesalmeida.carddemo.interest.InterestCalculator.Account;
import io.github.fabioalvesalmeida.carddemo.interest.InterestCalculator.CategoryBalance;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class InterestCalculatorTest {

    static BigDecimal d(String v) { return new BigDecimal(v); }

    static final InterestCalculator.RateTable RATES = (group, type, cat) -> {
        if (group.equals("GOLD") && type.equals("01") && cat == 1) return Optional.of(d("18.99"));
        if (group.equals("DEFAULT") && type.equals("01") && cat == 1) return Optional.of(d("24.00"));
        if (group.equals("DEFAULT") && type.equals("02") && cat == 2) return Optional.of(d("0.00"));
        return Optional.empty();
    };

    @Test // BR-CBACT04C-01: truncation, not rounding
    void monthlyInterestTruncates() {
        // 1000.00 * 18.99 / 1200 = 15.825 -> 15.82 (ROUNDED would give 15.83)
        assertEquals(d("15.82"), InterestCalculator.monthlyInterest(d("1000.00"), d("18.99")));
        assertEquals(d("-15.82"), InterestCalculator.monthlyInterest(d("-1000.00"), d("18.99")));
    }

    @Test // BR-CBACT04C-01: silent high-order truncation into S9(09)V99
    void monthlyInterestOverflowDropsHighOrderDigits() {
        BigDecimal huge = d("999999999.99");
        BigDecimal r = InterestCalculator.monthlyInterest(huge, d("9999.99"));
        assertEquals(2, r.scale());
        assertEquals(true, r.abs().compareTo(d("1000000000")) < 0);
    }

    @Test // BR-CBACT04C-03: DEFAULT fallback, then abend
    void rateLookupFallsBackToDefault() {
        var calc = new InterestCalculator(RATES);
        assertEquals(d("24.00"), calc.rateFor("SILVER", "01", 1));
        assertThrows(IllegalStateException.class, () -> calc.rateFor("SILVER", "09", 9));
    }

    @Test // BR-02, BR-04, BR-05 end to end
    void runPostsOncePerAccountAndWritesTransactions() {
        var calc = new InterestCalculator(RATES);
        var accounts = Map.of(
                1L, new Account(1L, "GOLD", d("500.00"), d("10.00"), d("20.00")),
                2L, new Account(2L, "SILVER", d("0.00"), d("1.00"), d("2.00")));
        var balances = List.of(
                new CategoryBalance(1L, "01", 1, d("1000.00")),   // 15.82
                new CategoryBalance(1L, "02", 2, d("300.00")),    // rate 0 -> skipped
                new CategoryBalance(2L, "01", 1, d("100.00")));   // DEFAULT 24.00 -> 2.00

        var result = calc.run("2026-10-21", balances, accounts);

        assertEquals(d("515.82"), result.updatedAccounts().get(1L).currentBalance());
        assertEquals(d("0.00"), result.updatedAccounts().get(1L).cycleCredit());
        assertEquals(d("0.00"), result.updatedAccounts().get(1L).cycleDebit());
        assertEquals(d("2.00"), result.updatedAccounts().get(2L).currentBalance());

        assertEquals(2, result.transactions().size());
        var t1 = result.transactions().get(0);
        assertEquals("2026-10-21000001", t1.transactionId());
        assertEquals("01", t1.typeCode());
        assertEquals(5, t1.categoryCode());
        assertEquals("Int. for a/c 00000000001", t1.description());
        assertEquals("2026-10-21000002", result.transactions().get(1).transactionId()); // suffix not reset
    }
}
