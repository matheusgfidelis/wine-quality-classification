// Gera o deck executivo a partir do JSON preparado por tools/build_deck.py
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");
const fs = require("fs");
const [, , dataPath, outPath] = process.argv;
const D = JSON.parse(fs.readFileSync(dataPath, "utf-8"));

const THEME = {
  name: "Vinho", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "2B2B2B", lt1: "FFFFFF", dk2: "4A1228", lt2: "F4ECEF", accent1: "8E1B3A", accent2: "C9A24B",
            accent3: "7F8C8D", accent4: "2E6F5E", accent5: "B5483A", accent6: "5B5B5B", hlink: "8E1B3A", folHlink: "7F8C8D" },
};
const H = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Classificação da qualidade de vinhos — apresentação executiva";
const C = pres.SchemeColor;

const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const pct = (x) => (x * 100).toFixed(1).replace(".", ",") + "%";
const lc = (s) => (/^(SO|pH)/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1));
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const join3 = (a) => `${a[0]}, ${a[1]} e ${a[2]}`;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "LIGHT", background: { color: H.lt1 },
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: C.accent3, fontSize: 11 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.4, w: 11.9, h: 1.2, fontSize: 32, bold: true,
    color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "DARK", background: { color: H.dk2 },
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: C.accent2, fontSize: 11 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.9, y: 1.9, w: 8.2, h: 2.4, fontSize: 44, bold: true,
    color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } }],
});

pres.defineSlideMaster({
  title: "CLOSE", background: { color: H.dk2 },
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: C.accent2, fontSize: 11 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.4, w: 11.9, h: 1.2, fontSize: 32, bold: true,
    color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } }],
});

// ---------- helpers ----------
const T = (s, text, x, y, w, h, o = {}) =>
  s.addText(text, Object.assign({ x, y, w, h, isTextBox: true, fontSize: 16, color: C.text1, valign: "top", margin: 0 }, o));
const card = (s, x, y, w, h, name) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: C.background2 }, line: { color: C.background2, width: 0 },
    rectRadius: 0.12, objectName: name || "card" });
const badge = (s, x, y, d, label, fill, txt, size = 18) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: "badge " + label });
  T(s, String(label), x, y, d, d, { align: "center", valign: "middle", bold: true, fontSize: size, color: txt });
};
const ens = (s) => { if (D.ensaio) T(s, `RESULTADOS DE ENSAIO — base ${D.base} (não é a base oficial)`, 0.7, 7.0, 9, 0.3, { fontSize: 11, color: C.accent5, bold: true }); };
let n = 0;
const slide = (master, section, title) => {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  n += 1;
  s.addText(title, { placeholder: "title" });
  if (D.notas[n]) s.addNotes(D.notas[n]);
  ens(s);
  return s;
};
["Contexto", "Análise exploratória", "Modelagem", "Decisão"].forEach((t) => pres.addSection({ title: t }));

// ---------- 1 · capa ----------
{
  const s = slide("DARK", "Contexto", "Dá para antecipar um grande vinho só pela química?");
  T(s, "Prevendo a qualidade de vinhos a partir de medidas de laboratório", 0.9, 4.45, 8.2, 0.9, { fontSize: 22, color: C.accent2 });
  T(s, "Tech Challenge · Fase 2 · Data Analytics", 0.9, 5.55, 8.2, 0.4, { fontSize: 16, color: C.background1 });
  s.addShape(pres.shapes.OVAL, { x: 9.6, y: 1.9, w: 3.0, h: 3.0, fill: { type: "none" }, line: { color: C.accent2, width: 3 }, objectName: "motivo nota 7" });
  T(s, "≥ 7", 9.6, 1.9, 3.0, 3.0, { align: "center", valign: "middle", fontSize: 66, bold: true, color: C.background1, fontFace: THEME.headFontFace });
  T(s, "nota que define um vinho de alta qualidade", 9.4, 5.1, 3.4, 0.7, { align: "center", fontSize: 14, color: C.background1 });
}

// ---------- 2 · problema ----------
{
  const s = slide("LIGHT", "Contexto", "O objetivo é priorizar a análise, não substituir o enólogo");
  const L = ["Medidas de laboratório", "Estimativa da chance de nota alta", "Lista de lotes priorizada", "Enólogo decide"];
  const S = ["acidez, álcool, sulfatos, SO₂…", `a partir de 11 medidas por vinho`, "quem merece degustação primeiro", "a decisão continua humana"];
  L.forEach((l, i) => {
    const x = 0.7 + i * 3.1;
    card(s, x, 2.0, 2.6, 2.4, "etapa " + (i + 1));
    badge(s, x + 0.25, 2.25, 0.6, i + 1, H.accent1, C.background1);
    T(s, l, x + 0.25, 3.0, 2.15, 0.8, { bold: true, fontSize: 17, color: C.text2 });
    T(s, S[i], x + 0.25, 3.8, 2.15, 0.5, { fontSize: 13, color: C.accent6 });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.67, y: 3.05, w: 0.36, h: 0.36, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: "seta " + (i + 1) });
  });
  T(s, "A nota do vinho é uma opinião humana. A estimativa serve de apoio à decisão — nunca de decisão automática.", 0.7, 5.0, 11.9, 1.0, { fontSize: 20, color: C.text1 });
}

// ---------- 3 · dados ----------
{
  const s = slide("LIGHT", "Contexto", `${fmt(D.n)} vinhos, 11 medidas químicas e uma nota de provadores`);
  const items = [[fmt(D.n), "vinhos tintos analisados"], ["11", "medidas físico-químicas por vinho"], ["0", "valores faltantes"],
                 [fmt(D.n_dup), `linhas repetidas (${pct(D.pct_dup)})`]];
  items.forEach((it, i) => {
    const x = 0.7 + i * 3.1;
    card(s, x, 2.0, 2.8, 2.9, "dado " + (i + 1));
    T(s, it[0], x + 0.25, 2.4, 2.3, 1.2, { fontSize: 54, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
    T(s, it[1], x + 0.25, 3.8, 2.3, 0.9, { fontSize: 16, color: C.text1 });
  });
  T(s, `Base: ${D.base} · notas de 3 a 8 · linhas repetidas removidas antes de avaliar os modelos`, 0.7, 5.4, 11.9, 0.5, { fontSize: 14, color: C.accent6 });
}

// ---------- 4 · definição e balanceamento ----------
{
  const s = slide("LIGHT", "Análise exploratória", `Alta qualidade = nota 7 ou mais — e só ${pct(D.pct_alta)} chegam lá`);
  s.addChart(pres.charts.BAR, [{ name: "Vinhos", labels: D.nota_labels, values: D.nota_vals }], {
    x: 0.6, y: 1.8, w: 7.3, h: 4.9, barDir: "col", chartColors: [H.accent3, H.accent3, H.accent3, H.accent3, H.accent1, H.accent1],
    showTitle: true, title: "Vinhos por nota (7 e 8 = alta qualidade)", titleFontSize: 14, titleFontFace: "+mn-lt", titleColor: H.dk1,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 13, dataLabelFontFace: "+mn-lt", dataLabelColor: H.dk1,
    catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: H.dk1, catGridLine: { style: "none" },
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: H.accent6, valGridLine: { color: "E5E5E5", size: 0.5 },
    showLegend: false, objectName: "gráfico notas",
  });
  card(s, 8.2, 1.9, 4.4, 2.0, "destaque 1");
  T(s, pct(D.pct_alta), 8.45, 2.0, 3.9, 1.0, { fontSize: 48, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
  T(s, `${fmt(D.n_alta)} de ${fmt(D.n)} vinhos são de alta qualidade`, 8.45, 3.1, 3.9, 0.7, { fontSize: 15 });
  card(s, 8.2, 4.15, 4.4, 2.5, "destaque 2");
  T(s, pct(1 - D.pct_alta), 8.45, 4.25, 3.9, 1.0, { fontSize: 48, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
  T(s, "é o acerto de quem chutasse sempre “não é de alta qualidade”. Por isso não julgamos só pelo percentual de acertos.", 8.45, 5.35, 3.9, 1.2, { fontSize: 14 });
}

// ---------- 5 · EDA: boxplots ----------
{
  const s = slide("LIGHT", "Análise exploratória", cap(`${join3(D.top3_nomes.map(lc))} separam melhor os bons vinhos`));
  const w = 11.4, h = w * D.dim_box[1] / D.dim_box[0];
  s.addImage({ path: D.fig_box, x: 0.95, y: 1.85, w, h, altText: "Boxplots das três variáveis por classe", objectName: "figura boxplots" });
  T(s, "Cada caixa mostra onde estão os 50% centrais dos vinhos. É associação — não prova que mudar a medida muda a nota.", 0.7, 6.3, 11.9, 0.6, { fontSize: 14, color: C.accent6 });
}

// ---------- 6 · EDA: correlações ----------
{
  const s = slide("LIGHT", "Análise exploratória", "Várias medidas andam juntas — por razões químicas");
  s.addChart(pres.charts.BAR, [{ name: "Associação com a nota", labels: D.corr_labels, values: D.corr_vals }], {
    x: 0.6, y: 1.7, w: 6.7, h: 5.1, barDir: "bar", chartColors: [H.accent1], invertedColors: [H.accent3],
    showTitle: true, title: "Associação de cada medida com a nota", titleFontSize: 14, titleFontFace: "+mn-lt", titleColor: H.dk1,
    showValue: true, dataLabelFormatCode: "0.00", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", dataLabelColor: H.dk1,
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: H.dk1, catAxisLabelPos: "low", catGridLine: { style: "none" },
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: H.accent6, valGridLine: { color: "E5E5E5", size: 0.5 },
    showLegend: false, objectName: "gráfico correlação com a nota",
  });
  D.pares.forEach((p, i) => {
    const y = 1.8 + i * 2.05;
    card(s, 7.7, y, 4.9, 1.9, "par " + (i + 1));
    T(s, `${p.var_a} × ${p.var_b}`, 7.95, y + 0.15, 4.4, 0.4, { bold: true, fontSize: 16, color: C.text2 });
    T(s, `força da relação: ${String(p.spearman).replace(".", ",")} (escala de −1 a 1)`, 7.95, y + 0.55, 4.4, 0.3, { fontSize: 12, color: C.accent6 });
    T(s, p.justificativa, 7.95, y + 0.95, 4.4, 0.9, { fontSize: 14 });
  });
  T(s, "Barras para a direita: mais comum nos vinhos bem avaliados; para a esquerda: menos comum. Medidas parecidas dividem o “peso” na previsão.", 7.7, 5.95, 4.9, 0.9, { fontSize: 13, color: C.accent6 });
}

// ---------- 7 · estratégia ----------
{
  const s = slide("LIGHT", "Modelagem", "Testamos três métodos sem “colar” na prova final");
  const st = [["Retirar vinhos repetidos", `${fmt(D.n_dup)} linhas idênticas`], ["Separar a prova final", `${fmt(D.n_teste)} vinhos (20%)`],
              ["Treinar e comparar", "só com os vinhos de treino"], ["Escolher o método", "sem olhar a prova final"],
              ["Provar uma única vez", `${D.n_alta_teste} bons vinhos na prova`]];
  st.forEach((a, i) => {
    const x = 0.7 + i * 2.45;
    badge(s, x, 2.1, 0.7, i + 1, H.accent1, C.background1, 22);
    T(s, a[0], x, 3.0, 2.2, 0.8, { bold: true, fontSize: 17, color: C.text2 });
    T(s, a[1], x, 3.85, 2.2, 0.8, { fontSize: 14, color: C.accent6 });
  });
  card(s, 0.7, 5.2, 11.9, 1.3, "métodos");
  T(s, "Três métodos de complexidade crescente: um estatístico clássico, um conjunto de regras “se… então” e um conjunto de muitas árvores que “votam” juntas.", 1.0, 5.4, 11.3, 0.9, { fontSize: 16 });
}

// ---------- 8 · comparação ----------
{
  const s = slide("LIGHT", "Modelagem", `O método escolhido encontra ${D.recall_esc}% dos bons vinhos — com alarmes falsos`);
  s.addChart(pres.charts.BAR, [
    { name: "Bons vinhos encontrados (%)", labels: D.modelos, values: D.recall },
    { name: "Indicações certas (%)", labels: D.modelos, values: D.precision },
  ], {
    x: 0.6, y: 1.7, w: 7.3, h: 5.1, barDir: "col", barGrouping: "clustered", chartColors: [H.accent1, H.accent3],
    showTitle: true, title: "Prova final — critério padrão", titleFontSize: 14, titleFontFace: "+mn-lt", titleColor: H.dk1,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", dataLabelColor: H.dk1,
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: H.dk1, catGridLine: { style: "none" },
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: H.accent6, valGridLine: { color: "E5E5E5", size: 0.5 },
    valAxisMinVal: 0, valAxisMaxVal: 100, showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: H.dk1,
    objectName: "gráfico comparação de modelos",
  });
  card(s, 8.3, 1.9, 4.3, 2.4, "método adotado");
  T(s, "Método adotado", 8.55, 2.05, 3.8, 0.4, { bold: true, fontSize: 16, color: C.text2 });
  T(s, cap(D.descr_modelo) + ".", 8.55, 2.55, 3.8, 1.6, { fontSize: 15 });
  card(s, 8.3, 4.55, 4.3, 2.1, "incerteza");
  T(s, "Margem de incerteza", 8.55, 4.7, 3.8, 0.4, { bold: true, fontSize: 16, color: C.text2 });
  T(s, `A prova final tem só ${D.n_alta_teste} bons vinhos: diferenças pequenas entre os métodos não são conclusivas.`, 8.55, 5.2, 3.8, 1.35, { fontSize: 15 });
}

// ---------- 9 · variáveis ----------
{
  const top = D.imp_labels.slice(-3).reverse().map(lc);
  const s = slide("LIGHT", "Modelagem", cap(`${join3(top)} pesam mais nas previsões`));
  s.addChart(pres.charts.BAR, [{ name: "Importância", labels: D.imp_labels, values: D.imp_vals }], {
    x: 0.6, y: 1.7, w: 6.9, h: 5.1, barDir: "bar", chartColors: [H.accent1],
    showTitle: true, title: "Quanto o método piora sem a medida", titleFontSize: 14, titleFontFace: "+mn-lt", titleColor: H.dk1,
    showValue: true, dataLabelFormatCode: "0.000", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", dataLabelColor: H.dk1,
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: H.dk1, catGridLine: { style: "none" },
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: H.accent6, valGridLine: { color: "E5E5E5", size: 0.5 },
    showLegend: false, objectName: "gráfico importância das variáveis",
  });
  card(s, 7.9, 1.9, 4.7, 2.7, "direção observada");
  T(s, "O que se observa nos dados", 8.15, 2.05, 4.2, 0.4, { bold: true, fontSize: 16, color: C.text2 });
  T(s, D.direcoes.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < D.direcoes.length - 1 } })), 8.15, 2.55, 4.2, 1.95, { fontSize: 14, paraSpaceAfter: 6 });
  card(s, 7.9, 4.85, 4.7, 1.8, "importância não é causa");
  T(s, "Peso na previsão não é causa", 8.15, 5.0, 4.2, 0.4, { bold: true, fontSize: 16, color: C.text2 });
  T(s, "Mostra o que o método usa para prever, não o que faz um vinho melhor.", 8.15, 5.45, 4.2, 1.1, { fontSize: 14 });
}

// ---------- 10 · implicações ----------
{
  const s = slide("LIGHT", "Decisão", "Como usar isso na operação — hipóteses a validar");
  const cs = [["Priorizar a fila de degustação", "Lotes com maior chance estimada de nota alta vão primeiro."],
              ["Monitorar as medidas-chave", `Acompanhar ${join3(D.imp_labels.slice(-3).reverse().map(lc))} como indicadores de alerta.`],
              ["Investigar lotes fora do perfil", "Comparar cada lote com o perfil dos vinhos bem avaliados."]];
  cs.forEach((c, i) => {
    const x = 0.7 + i * 4.05;
    card(s, x, 2.0, 3.8, 3.3, "ação " + (i + 1));
    badge(s, x + 0.3, 2.3, 0.65, i + 1, H.accent1, C.background1, 20);
    T(s, c[0], x + 0.3, 3.2, 3.2, 0.9, { bold: true, fontSize: 18, color: C.text2 });
    T(s, c[1], x + 0.3, 4.1, 3.2, 1.1, { fontSize: 15 });
  });
  T(s, "As ligações observadas são associações: antes de mudar o processo, testar de forma controlada. O ganho financeiro ainda não foi medido.", 0.7, 5.7, 11.9, 0.9, { fontSize: 16, color: C.accent6 });
}

// ---------- 11 · limites e próximos passos ----------
{
  const s = slide("CLOSE", "Decisão", "Limites e próximos passos: um piloto com revisão humana");
  T(s, "O que ainda não sabemos", 0.7, 1.85, 5.6, 0.5, { bold: true, fontSize: 20, color: C.accent2, fontFace: THEME.headFontFace });
  T(s, "Próximos passos", 7.0, 1.85, 5.6, 0.5, { bold: true, fontSize: 20, color: C.accent2, fontFace: THEME.headFontFace });
  const L = [`Poucos bons vinhos: ${fmt(D.n_alta)} no total e ${D.n_alta_teste} na prova final`, "Uma só origem: vinho tinto português",
             "A nota é opinião de provadores", "Ganho financeiro e custo dos erros ainda não medidos"];
  const P = ["Piloto: comparar as previsões com o julgamento dos enólogos em novos lotes",
             "Definir o equilíbrio entre bons vinhos achados e alarmes falsos, com base em custos",
             "Validar com outras safras e produtores", "Acompanhar o desempenho ao longo do tempo"];
  L.forEach((t, i) => {
    const y = 2.6 + i * 1.05;
    badge(s, 0.7, y, 0.5, "!", H.accent2, C.text2, 18);
    T(s, t, 1.45, y - 0.2, 4.8, 0.9, { fontSize: 16, color: C.background1, valign: "middle" });
  });
  P.forEach((t, i) => {
    const y = 2.6 + i * 1.05;
    badge(s, 7.0, y, 0.5, i + 1, H.accent2, C.text2, 18);
    T(s, t, 7.75, y - 0.2, 4.85, 0.9, { fontSize: 16, color: C.background1, valign: "middle" });
  });
}

(async () => {
  await pres.writeFile({ fileName: outPath });
  await applyTheme(outPath, THEME);
  console.log("ok", outPath);
})();
