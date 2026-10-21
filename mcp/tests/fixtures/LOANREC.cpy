      * Synthetic copybook written for this repository (RECLN 40)
       01  LOAN-RECORD.
           05  LOAN-ID                PIC 9(08).
           05  LOAN-PRINCIPAL         PIC S9(09)V99 COMP-3.
           05  LOAN-RATE              PIC S9(03)V9(4).
           05  LOAN-TERMS             OCCURS 3 TIMES.
               10  TERM-MONTHS        PIC 9(03).
           05  LOAN-STATUS            PIC X(01).
               88  LOAN-ACTIVE        VALUE 'A'.
           05  LOAN-ALT REDEFINES LOAN-STATUS PIC X(01).
           05  FILLER                 PIC X(09).
