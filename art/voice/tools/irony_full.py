"""Full voice-over 2026-10-07: lines read as dry irony / sarcasm (they get casting.IRONY in the style prompt).

Classified by reading every new line, with the rule of the recast (recast.DELIVERY): a line counts when its humour
lives in a wry twist the speaker means (self-irony, a dry comeback or punchline, mock-seriousness, understatement,
an ironic question). Set-up questions, sincere lines, instructions and plain information do not count. Not marked
on purpose: the children (Tóno 12, Jana 12, Zuzana 7, Soňa, Kubo, Adam 10: their humour is literal child logic, said
seriously), Očko the robot (comedy from being literal, deadpan synthetic), Viktor, Lea, the narrator and SYSTEM
(serious by design), Rudo's stage exclamations and the tender lines of the endings.
"""

IRONY_IDS = """
action.C03.x02 action.C03.x03 action.C03.x05 action.C02.x01 action.C02.x02 action.C04.x02 topic.ELA.extra 2.002
action.G05.x04 action.C01.x01 action.C01.x02 action.C01.x05 action.C01.x06 action.C01.x08 topic.MIRA20.after.004
topic.MIRA20.after.x02 topic.MIRA20.extra 3.004 action.C05.002 cutscene.CS05.01.002 cutscene.CS05.02.002
travel.S07.to_S51.first.002 action.D04.002 entry.S54.001 action.D02.x06 action.D07.002 topic.TONO20.ambient 1.x02
topic.TONO20.ambient 2.x01 topic.TONO20.ambient 2.x03 topic.TONO20.extra 2.004 topic.TONO20.extra 3.004
action.D03.x02 action.Q9E.x02 topic.JANA20.ambient 1.x03 topic.JANA20.extra 1.004 topic.JANA20.extra 2.004
action.D06.002 topic.JOZEF.extra 3.002 topic.JOZEF.extra 3.004 entry.S12.001 action.B01.001 action.B01.002
entry.S13.001 action.B02.x01 action.B02.x02 action.B02.x04 action.B02.005 action.B02.x05 action.B02.x06
action.E11.003 action.E11.x03 action.E11.008 action.Q5B.x01 action.Q5B.002 action.Q5B.003 action.Q5B.x03
topic.TONO.ambient 1.003 topic.TONO.ambient 1.x01 topic.TONO.ambient 1.x03 topic.TONO.ambient 2.002
topic.TONO.ambient 2.x01 topic.TONO.ambient 2.x03 topic.TONO.extra 1.006 topic.TONO.extra 2.003
topic.TONO.extra 2.005 topic.TONO.extra 3.004 entry.S14.001 action.B03.x04 action.B03.x05 action.B03.x06
action.B03.x07 action.B03.006 action.B03.x08 topic.MIRA95.ambient 1.x03 topic.MIRA95.ambient 2.x02
topic.MIRA95.ambient 2.002 topic.MIRA95.ambient 2.003 topic.MIRA95.extra 2.004 topic.MIRA95.extra 3.002
topic.LEA95.ambient 1.003 topic.LEA95.after.x03 topic.LEA95.ambient 2.002 topic.LEA95.extra 2.001 entry.S15.001
action.Q9D.x04 topic.JANA95.ambient 1.x01 topic.JANA95.ambient 1.x03 topic.JANA95.extra 1.004
topic.JANA95.extra 1.005 topic.JANA95.extra 1.006 entry.S16.001 entry.S11.001 action.B18.x01 action.B18.x04
action.B18.004 action.B18.x05 action.Q4A.x04 topic.EMIL.ambient 1.002 topic.EMIL.ambient 1.x02
topic.EMIL.ambient 1.x03 topic.EMIL.ambient 2.002 topic.EMIL.ambient 2.x03 topic.EMIL.extra 1.004
topic.EMIL.extra 2.004 action.B05.x02 action.B05.004 action.B05.005 action.B05.x04 action.B05.k01
topic.PALI.ambient 1.003 topic.PALI.ambient 1.x01 topic.PALI.ambient 1.x03 topic.PALI.ambient 2.002
topic.PALI.ambient 2.003 topic.PALI.ambient 2.x01 topic.PALI.ambient 2.x02 topic.PALI.extra 1.002
topic.PALI.extra 1.004 topic.PALI.extra 1.006 topic.PALI.extra 2.002 topic.PALI.extra 2.004 entry.S21.001
entry.S25.001 entry.S27.001 action.B08.x02 action.B08.x03 action.B08.x04 action.B08.x05 topic.TRH.ambient 1.001
topic.TRH.ambient 1.x01 topic.TRH.ambient 1.x02 topic.TRH.ambient 1.x03 topic.TRH.ambient 2.002
topic.TRH.ambient 2.003 topic.TRH.ambient 2.x02 topic.TRH.extra 1.004 topic.TRH.extra 2.002 topic.TRH.extra 2.004
action.B07.002 topic.JURO.ambient 1.001 topic.JURO.ambient 1.002 topic.JURO.ambient 1.x03 topic.JURO.extra 1.004
topic.JURO.extra 2.002 topic.JURO.extra 2.004 action.B09.x02 action.B09.x05 topic.MILADA.ambient 1.002
topic.MILADA.ambient 1.x03 topic.MILADA.ambient 2.x01 topic.MILADA.ambient 2.x02 topic.MILADA.ambient 2.x03
topic.MILADA.extra 1.002 topic.MILADA.extra 1.004 topic.MILADA.extra 2.004
entry.S23.001 action.B13.x02 action.B13.x04 action.B13.004 action.B13.k01 action.B13.x06
topic.ARCHIVAR.ambient 1.x02 topic.ARCHIVAR.ambient 2.002 topic.ARCHIVAR.ambient 2.x02 topic.ARCHIVAR.extra 1.004
topic.ARCHIVAR.extra 2.004 topic.ARCHIVAR.extra 2.006 entry.S24.001 action.B14.x02 action.B14.004 action.B14.x04
action.Q3C.003 action.Q3C.004 action.Q3C.x04 action.Q3C.x05 topic.FOTO.ambient 1.003 topic.FOTO.ambient 1.x01
topic.FOTO.ambient 2.002 topic.FOTO.ambient 2.x03 topic.FOTO.extra 1.002 topic.FOTO.extra 2.002 entry.S22.001
action.B15.x02 action.B15.003 action.B15.x03 action.B16.002 action.Q4B.002 action.Q4B.x03 topic.VIERA.ambient 1.002
topic.VIERA.ambient 1.003 topic.VIERA.ambient 1.x01 topic.VIERA.ambient 1.x02 topic.VIERA.ambient 1.x03
topic.VIERA.ambient 2.x02 topic.VIERA.extra 1.002 topic.VIERA.extra 1.004 topic.JURAJ.ambient 2.002
topic.JURAJ.ambient 2.x03 topic.JURAJ.extra 1.003 entry.S29.001 action.B17.x02 action.B17.004
topic.DEZI.ambient 1.x01 topic.DEZI.ambient 2.x03 topic.DEZI.extra 1.004 topic.DEZI.extra 1.006
topic.DEZI.extra 2.004 topic.DEZI.extra 2.005 topic.DEZI.extra 2.006 entry.S17.001 action.Q3D.002 action.Q3D.004
action.Q3D.x04 topic.SONA.ambient 2.x03 action.B19.002 action.B19.z04 action.Q11A.007 topic.ZUZANA95.extra 1.009
topic.ZUZANA95.extra 1.010 topic.ZUZANA95.extra 3.006 topic.ZUZANA95.extra 3.007 topic.ZUZANA95.extra 5.004
topic.ZUZANA95.extra 5.005 topic.ZUZANA95.extra 5.006 topic.ZUZANA95.extra 6.006 topic.ZUZANA95.extra 6.007
topic.KUBO.extra 1.005 entry.S30.001 action.B22.003 entry.S18.001 action.Q3B.003 action.Q3B.x02 action.Q3B.x04
topic.ZITA.ambient 1.002 topic.ZITA.ambient 1.x02 topic.ZITA.ambient 2.x03 topic.ZITA.extra 1.006
topic.ZITA.extra 2.004
entry.S31.001 topic.BOZO.ambient 1.002 topic.BOZO.ambient 1.x01 topic.BOZO.ambient 2.004 topic.BOZO.ambient 2.x02
topic.BOZO.extra 1.002 topic.BOZO.extra 1.004 topic.BOZO.extra 2.005 topic.BOZO.extra 2.007 topic.BOZO.extra 3.004
entry.S32.001 topic.BERTA.ambient 1.003 topic.BERTA.ambient 1.x02 topic.BERTA.ambient 1.x04 topic.BERTA.ambient 2.x02
topic.BERTA.ambient 2.x03 topic.BERTA.extra 1.004 topic.BERTA.extra 1.006 topic.BERTA.extra 2.004
topic.BERTA.extra 2.007 entry.S35.001 action.I02.002 action.I02.003 action.I02.x05 action.Q6B.002 action.Q6B.x02
action.Q10B.004 topic.SKLAD.ambient 1.001 topic.SKLAD.ambient 1.x03 topic.SKLAD.ambient 2.x03 topic.SKLAD.extra 1.004
topic.SKLAD.extra 2.005 action.I01.004 action.I01.005 action.I01.x07 action.I01.x05 action.I07.x02
topic.OTO.ambient 1.x01 topic.OTO.ambient 1.x03 topic.OTO.ambient 2.x02 topic.OTO.extra 1.006 topic.OTO.extra 2.004
topic.OTO.extra 2.006 topic.OTO.extra 3.004 entry.S34.001 action.I03.z03 action.I03.004 action.I03.x02
action.Q7C.003 action.Q7C.004 action.Q7C.x05 topic.LIDA.ambient 1.003 topic.LIDA.ambient 1.x02 topic.LIDA.ambient 2.002
topic.LIDA.ambient 2.x01 topic.LIDA.ambient 2.x03 topic.LIDA.extra 1.004 topic.LIDA.extra 2.005
topic.RUDO.ambient 1.002 topic.RUDO.ambient 2.002 topic.RUDO.extra 1.003 topic.RUDO.extra 2.004 action.I10.z02
action.I10.003 action.I10.004 action.Q6C.002 action.Q10D.004 topic.VERA60.ambient 1.002 topic.VERA60.ambient 1.x03
topic.VERA60.ambient 2.002 topic.VERA60.ambient 2.x01 topic.VERA60.ambient 2.x02 topic.VERA60.extra 1.004
topic.VERA60.extra 3.003 topic.VERA60.extra 3.004 topic.VERA60.extra 2.002 topic.VERA60.extra 2.004
topic.ZUZANA.extra 7.006 entry.S38.001 action.I08.001 entry.S39.001 action.I09.x03 action.I09.x04
topic.MIRA60.ambient 1.003 topic.MIRA60.ambient 1.x01 topic.MIRA60.ambient 1.x03 topic.MIRA60.ambient 2.002
topic.MIRA60.ambient 2.x02 topic.MIRA60.ambient 2.x03 topic.MIRA60.extra 3.002 entry.S40.001 action.I17.x02
action.Q7B.001 entry.S33.001 action.I14.002 action.I14.x03 action.I16.x02 action.I16.003 action.Q6A.002
action.Q6A.003 action.Q6D.x01 action.Q6D.x02 action.Q6D.x03 epilogue.6.line topic.POSTA.ambient 1.001
topic.POSTA.ambient 1.x01 topic.POSTA.ambient 2.x03 topic.POSTA.extra 1.005 topic.POSTA.extra 2.004
entry.S41.001 action.F01.x07 action.F01.x08 action.F01.x09 topic.NINA.ambient 1.001 topic.NINA.ambient 1.002
topic.NINA.ambient 1.x01 topic.NINA.ambient 1.x03 topic.NINA.after.x02 topic.NINA.after.x04 topic.NINA.extra 2.004
topic.NINA.extra 2.006 topic.NINA.extra 3.002 topic.NINA.extra 3.005 topic.NINA.extra 3.006 entry.S43.001
action.F02.x01 action.F02.003 action.F02.x04 action.F02.x06 action.F02.x07 action.Q8C.x02 action.Q8C.x03
action.Q8C.x05 topic.TAMARA.ambient 1.001 topic.TAMARA.ambient 1.003 topic.TAMARA.ambient 1.x04
topic.TAMARA.ambient 2.x02 topic.TAMARA.ambient 2.x03 topic.TAMARA.extra 2.004 topic.TAMARA.extra 3.004
topic.TAMARA.extra 1.006 action.F03.x02 action.F03.x08 action.Q9F.x03 action.Q9F.x05 topic.BORIS.ambient 2.002
topic.BORIS.ambient 2.x03 topic.BORIS.extra 1.002 topic.BORIS.extra 1.004 topic.BORIS.extra 1.005
topic.BORIS.extra 1.006 topic.BORIS.extra 2.004 topic.JANA35.ambient 1.001 topic.JANA35.ambient 1.002
topic.JANA35.ambient 1.x03 topic.JANA35.extra 1.002 topic.JANA35.extra 1.004 topic.JANA35.extra 1.006
entry.S46.001 action.F04.004 action.F04.x05 action.F04.x06 topic.SARA.ambient 1.002 topic.SARA.ambient 1.003
topic.SARA.ambient 1.x02 topic.SARA.ambient 1.x03 topic.SARA.ambient 2.x03 topic.SARA.extra 1.006
topic.SARA.extra 2.003 entry.S67.001 action.J03.x03 action.J03.002 topic.IVAN.ambient 1.002 topic.IVAN.ambient 2.x01
topic.IVAN.ambient 2.x03 topic.IVAN.extra 1.004 topic.IVAN.extra 1.006 topic.IVAN.extra 2.003 topic.IVAN.extra 2.004
entry.S68.001 action.J04.002 action.J04.x01 action.J04.x02 topic.TURISTA.ambient 1.x01 topic.TURISTA.ambient 1.x04
topic.TURISTA.ambient 2.x03 topic.TURISTA.extra 1.004 topic.TURISTA.extra 2.002 topic.TURISTA.extra 2.004
entry.S47.001 entry.S48.001 action.F06.x02 action.F06.005 action.F08.x04 action.F08.x05 action.F09.004
action.F09.x02 entry.S50.001
entry.S57.001 action.E08.005 action.E08.x05 entry.S64.001 action.E01.004 action.E01.005 action.E01.x04
action.E02.003 topic.TONO82.ambient 1.002 topic.TONO82.extra 1.005 topic.TONO82.extra 2.005
topic.OTO82.ambient 1.002 topic.OTO82.ambient 1.003 topic.OTO82.ambient 1.x01 topic.OTO82.ambient 1.x03
topic.OTO82.ambient 2.x01 topic.OTO82.ambient 2.x03 topic.OTO82.extra 1.002 topic.OTO82.extra 1.004
topic.OTO82.extra 1.005 topic.OTO82.extra 1.006 topic.OTO82.extra 2.004 topic.OTO82.extra 3.003 action.E05.x04
action.E05.x05 topic.RUZENA.ambient 1.x03 topic.RUZENA.ambient 2.x03 topic.RUZENA.extra 1.006 topic.RUZENA.extra 3.004
entry.S65.001 action.E03.x02 action.E03.003 action.E03.x05 topic.MARTA82.ambient 1.x01 topic.MARTA82.ambient 1.x02
topic.MARTA82.ambient 1.x03 topic.MARTA82.ambient 2.x01 topic.MARTA82.ambient 2.x02 topic.MARTA82.ambient 2.x03
topic.MARTA82.extra 2.004 entry.S59.001 entry.S63.001 entry.S66.001 action.E07.x03 action.E10.004 action.E10.x01
topic.SIMON.ambient 1.002 topic.SIMON.ambient 1.x01 topic.SIMON.ambient 2.x03 topic.SIMON.extra 1.006
topic.SIMON.extra 2.002 entry.S60.001 topic.DOBRO.ambient 1.x03 topic.DOBRO.ambient 2.002 topic.DOBRO.ambient 2.x01
topic.DOBRO.ambient 2.x03 topic.DOBRO.extra 1.006
"""


def _parse(block: str) -> set[str]:
    """Ids contain spaces ("topic.TONO.ambient 1.003"): split on the id starts."""
    import re
    starts = r"(?=\b(?:action|topic|entry|cutscene|travel|epilogue)\.)"
    return {p.strip() for p in re.split(starts, block.replace("\n", " ")) if p.strip()}


IRONY = _parse(IRONY_IDS)
