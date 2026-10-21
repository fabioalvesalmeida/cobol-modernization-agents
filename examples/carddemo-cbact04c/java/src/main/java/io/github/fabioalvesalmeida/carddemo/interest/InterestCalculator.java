package io.github.fabioalvesalmeida.carddemo.interest;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Java implementation of CardDemo batch program CBACT04C (monthly interest posting).
 *
 * <p>Each method names the Business Rule Card rule it implements
 * ({@code examples/carddemo-cbact04c/business-rule-card.json}). I/O is abstracted behind
 * {@link RateTable} so the same logic runs in batch, in a Quarkus service, or in equivalence tests.
 */
public final class InterestCalculator {

    static final BigDecimal DIVISOR = BigDecimal.valueOf(1200);
    static final String DEFAULT_GROUP = "DEFAULT";

    /** Disclosure-group rate lookup by (group id, transaction type code, category code). */
    public interface RateTable {
        Optional<BigDecimal> find(String groupId, String typeCode, int categoryCode);
    }

    /** One TRAN-CAT-BAL record (copybook CVTRA01Y). */
    public record CategoryBalance(long accountId, String typeCode, int categoryCode, BigDecimal balance) {}

    /** Account fields touched by the program (copybook CVACT01Y). */
    public record Account(long accountId, String groupId, BigDecimal currentBalance,
                          BigDecimal cycleCredit, BigDecimal cycleDebit) {}

    /** One generated interest transaction (subset of CVTRA05Y). */
    public record InterestTransaction(String transactionId, long accountId, String typeCode,
                                      int categoryCode, String source, String description,
                                      BigDecimal amount) {}

    static final String INTEREST_TYPE_CODE = "01";
    static final int INTEREST_CATEGORY_CODE = 5;

    public record Result(Map<Long, Account> updatedAccounts, List<InterestTransaction> transactions) {}

    private final RateTable rates;

    public InterestCalculator(RateTable rates) {
        this.rates = rates;
    }

    /** BR-CBACT04C-01: (balance * rate) / 1200, stored in S9(09)V99 with truncation. */
    public static BigDecimal monthlyInterest(BigDecimal balance, BigDecimal annualRatePercent) {
        BigDecimal exact = balance.multiply(annualRatePercent).divide(DIVISOR, 10, java.math.RoundingMode.DOWN);
        return CobolDecimal.store(exact, 9, 2);
    }

    /** BR-CBACT04C-03: look up the rate, falling back to the DEFAULT group. */
    BigDecimal rateFor(String groupId, String typeCode, int categoryCode) {
        return rates.find(groupId, typeCode, categoryCode)
                .or(() -> rates.find(DEFAULT_GROUP, typeCode, categoryCode))
                .orElseThrow(() -> new IllegalStateException(
                        "ERROR READING DEFAULT DISCLOSURE GROUP for type " + typeCode + " category " + categoryCode));
    }

    /**
     * Process category balances in file order (sorted by account id, as the program assumes).
     *
     * @param runDate   PARM-DATE used as the transaction id prefix
     * @param balances  TCATBAL-FILE records
     * @param accounts  ACCOUNT-FILE records by id
     */
    public Result run(String runDate, List<CategoryBalance> balances, Map<Long, Account> accounts) {
        Map<Long, Account> updated = new LinkedHashMap<>();
        List<InterestTransaction> transactions = new ArrayList<>();
        Long currentAccount = null;
        BigDecimal totalInterest = BigDecimal.ZERO.setScale(2);
        int suffix = 0;

        for (CategoryBalance cb : balances) {
            if (currentAccount != null && cb.accountId() != currentAccount) {
                updated.put(currentAccount, post(accounts.get(currentAccount), totalInterest));   // BR-04
                totalInterest = BigDecimal.ZERO.setScale(2);
            }
            currentAccount = cb.accountId();
            Account account = accounts.get(cb.accountId());
            if (account == null) {
                throw new IllegalStateException("ACCOUNT NOT FOUND: " + cb.accountId());
            }
            BigDecimal rate = rateFor(account.groupId(), cb.typeCode(), cb.categoryCode());
            if (rate.signum() != 0) {                                                              // BR-02
                BigDecimal interest = monthlyInterest(cb.balance(), rate);                         // BR-01
                totalInterest = CobolDecimal.store(totalInterest.add(interest), 9, 2);
                suffix++;
                transactions.add(new InterestTransaction(                                         // BR-05
                        transactionId(runDate, suffix), cb.accountId(), INTEREST_TYPE_CODE,
                        INTEREST_CATEGORY_CODE, "System",
                        "Int. for a/c " + String.format("%011d", cb.accountId()), interest));
                // BR-06: fee computation is not implemented in the source program.
            }
        }
        if (currentAccount != null) {
            updated.put(currentAccount, post(accounts.get(currentAccount), totalInterest));
        }
        return new Result(updated, transactions);
    }

    /** BR-CBACT04C-05: PARM-DATE X(10) followed by WS-TRANID-SUFFIX 9(06), into TRAN-ID X(16). */
    static String transactionId(String runDate, int suffix) {
        String date = String.format("%-10s", runDate).substring(0, 10);
        return date + String.format("%06d", suffix % 1_000_000);
    }

    /** BR-CBACT04C-04: add total interest to the balance and reset cycle credit/debit. */
    static Account post(Account a, BigDecimal totalInterest) {
        BigDecimal newBalance = CobolDecimal.store(a.currentBalance().add(totalInterest), 10, 2);
        BigDecimal zero = BigDecimal.ZERO.setScale(2);
        return new Account(a.accountId(), a.groupId(), newBalance, zero, zero);
    }
}
