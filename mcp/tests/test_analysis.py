from pathlib import Path

from cobol_tools.analysis import extract_paragraph, parse_copybook, parse_data_items, program_structure, read_source

FX = Path(__file__).parent / "fixtures"


def field(fields, name):
    return next(f for f in fields if f["name"] == name)


def test_copybook_layout_and_types():
    f = parse_copybook(FX / "LOANREC.cpy")
    assert field(f, "LOAN-ID")["java_type"] == "int"
    p = field(f, "LOAN-PRINCIPAL")
    assert (p["digits"], p["scale"], p["length"], p["offset"]) == (11, 2, 6, 8)   # COMP-3: ceil(12/2)
    r = field(f, "LOAN-RATE")
    assert (r["digits"], r["scale"], r["length"], r["java_type"]) == (7, 4, 7, "java.math.BigDecimal")
    assert field(f, "LOAN-TERMS")["occurs"] == 3
    assert field(f, "LOAN-ALT")["offset"] == field(f, "LOAN-STATUS")["offset"]      # REDEFINES
    assert not any(x["name"] == "LOAN-ACTIVE" for x in f)                         # 88-levels skipped


def test_record_length_matches_declared_recln():
    root = parse_data_items(read_source(FX / "LOANREC.cpy"))[0]
    assert root.length == 40   # 8 + 6 + 7 + 3*3 + 1 + 9


def test_program_structure():
    s = program_structure(FX / "PAYCALC.cbl")
    assert s["program_id"] == "PAYCALC" and s["kind"] == "batch"
    assert s["copybooks"] == ["LOANREC"]
    assert s["files"][0]["dd"] == "LOANIN"
    names = [p["name"] for p in s["paragraphs"]]
    assert names == ["(MAIN)", "1000-OPEN", "2000-CALC"]
    main = s["paragraphs"][0]
    assert main["performs"] == ["1000-OPEN", "2000-CALC"]
    calc = s["paragraphs"][2]
    assert len(calc["computations"]) == 2


def test_extract_paragraph_skips_comments():
    p = extract_paragraph(FX / "PAYCALC.cbl", "2000-CALC")
    assert "COMPUTE WS-PAYMENT" in p["source"]
    assert "approximation" not in p["source"]
