import sys
sys.path.insert(0, "/home/claude/scripts")
from frames import *  # noqa

O = sys.argv[1]
P2, P3, P5, P6 = (f"/home/claude/frames/hi-{n}.png" for n in (2, 3, 5, 6))
T, S = "RAIO-X", "RONALDO SOUZA · ZAGUEIRO"
SRC = "Fonte: relatório FootFuturo · 1 jogo · 94 min"
SRC2 = "Fonte: relatório Scout Analytics · 1 jogo · 94 min"

# 01 gancho
text_frame(f"{O}/r01_gancho.jpg",
           [[("100% NO ALTO.", CYAN)], [("100% NO 1x1.", CYAN)], [("MAS SÓ 25s", AMBER)], [("COM A BOLA.", WHITE)]],
           size=150, tag=T, subject=S)
# 02 posse (relatório)
card_frame(f"{O}/r02_posse.jpg", T, S,
           [[("94 MINUTOS.", WHITE)], [("25 SEGUNDOS", AMBER)], [("COM A BOLA.", WHITE)]],
           P5, (88, 322, 836, 462), AMBER, SRC2, hl_boxes=[(101, 361, 196, 412)], zoom_box=(97, 357, 276, 414), zoom_w=720)
# 03 bordão
open_card(f"{O}/r03_bordao.jpg", "RAIO-X", "RONALDO SOUZA")
# 04 ficha
photo_frame(f"{O}/r04_ficha.jpg", T, S,
            [[("RONALDO SOUZA", WHITE)], [("ZAGUEIRO · 28 ANOS", CYAN)]],
            "/home/claude/foto/ronaldo_souza_ficha.jpg", "Ficha do atleta · relatório FootFuturo")
# 05 amostra
card_frame(f"{O}/r05_amostra.jpg", T, S,
           [[("1 JOGO SÓ.", AMBER)], [("PERFIL,", WHITE)], [("NÃO SENTENÇA.", WHITE)]],
           P2, (60, 55, 865, 172), AMBER, SRC, hl_boxes=[(470, 62, 662, 168)], zoom_box=(468, 58, 664, 170), zoom_w=600)
# 06 jogo aéreo
card_frame(f"{O}/r06_aereo.jpg", T, S,
           [[("JOGO AÉREO:", WHITE)], [("6 DE 6", CYAN)], [("ELITE: 78%", WHITE)]],
           P6, (110, 861, 815, 956), CYAN, SRC2, hl_boxes=[(750, 891, 790, 930)], zoom_box=(655, 869, 805, 932), zoom_w=720)
# 07 1x1
card_frame(f"{O}/r07_1x1.jpg", T, S,
           [[("NO 1x1:", WHITE)], [("9 DUELOS.", CYAN)], [("9 VITÓRIAS.", CYAN)]],
           P2, (63, 748, 557, 862), CYAN, SRC, hl_boxes=[(70, 752, 380, 802)], zoom_box=(68, 752, 382, 802), zoom_w=940)
# 08 interceptações (gráfico próprio: contagem bruta)
bars_frame(f"{O}/r08_interceptacoes.jpg", T, S,
           [[("INTERCEPTAÇÕES:", WHITE)], [("14 DE 17", CYAN)]],
           [("Aproveitamento", 82, 82, CYAN)], "Fonte: contagem bruta do relatório · 1 jogo",
           note="82% = exatamente a linha de elite")
# 09 mental
card_frame(f"{O}/r09_mental.jpg", T, S,
           [[("0 FALTAS. 0 CARTÕES.", WHITE)], [("RESILIÊNCIA", CYAN)], [("10/10", CYAN)]],
           P3, (585, 815, 834, 1000), CYAN, SRC, card_w=760)
# 10 virada
text_frame(f"{O}/r10_virada.jpg", [[("ONDE ELE", WHITE)], [("PERDE", AMBER)], [("TERRENO.", AMBER)]],
           size=190, tag=T, subject=S, color_bar=AMBER)
# 11 antecipação
card_frame(f"{O}/r11_antecipacao.jpg", T, S,
           [[("ANTECIPAÇÃO:", WHITE)], [("1 EM 3", AMBER)], [("ELITE: 83%", WHITE)]],
           P6, (110, 462, 815, 556), AMBER, SRC2, hl_boxes=[(750, 492, 790, 531)], zoom_box=(655, 470, 805, 532), zoom_w=720)
# 12 construção
card_frame(f"{O}/r12_construcao.jpg", T, S,
           [[("11 PASSES", AMBER)], [("EM 94 MINUTOS.", WHITE)], [("24% DO VOLUME.", AMBER)]],
           P2, (63, 748, 557, 862), AMBER, SRC, hl_boxes=[(70, 803, 395, 852)], zoom_box=(68, 803, 397, 852), zoom_w=940)
# 13 plano
list_frame(f"{O}/r13_plano.jpg", T, S, "PLANO DE TREINO",
           [("ANTECIPAÇÃO", "Ler o corpo do passador"),
            ("SAÍDA DE BOLA", "Oferecer linha sob pressão"),
            ("DADOS FÍSICOS", "Velocidade, distância, sprints")],
           "Sugestão a partir do relatório · 1 jogo")
# 14 final
end_card(f"{O}/r14_final.jpg", [("QUER ESSA ANÁLISE", WHITE), ("NO SEU ATLETA OU TIME?", CYAN)], "CHAMA NO DIRECT")
