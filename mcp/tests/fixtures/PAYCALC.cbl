      *> Synthetic test program written for this repository.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYCALC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOAN-FILE ASSIGN TO LOANIN
                  ORGANIZATION IS SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  LOAN-FILE.
       01  FD-LOAN-REC                PIC X(40).
       WORKING-STORAGE SECTION.
       COPY LOANREC.
       01  WS-PAYMENT                 PIC S9(07)V99.
       01  WS-COUNT                   PIC 9(05) COMP VALUE 0.
       PROCEDURE DIVISION.
           PERFORM 1000-OPEN
           PERFORM 2000-CALC UNTIL WS-COUNT > 10
           STOP RUN.
       1000-OPEN.
           OPEN INPUT LOAN-FILE.
       2000-CALC.
      * monthly payment approximation
           COMPUTE WS-PAYMENT = LOAN-PRINCIPAL * LOAN-RATE / 1200
           ADD 1 TO WS-COUNT.
