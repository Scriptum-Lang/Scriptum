from __future__ import annotations

from collections import defaultdict, OrderedDict
from typing import Dict, Iterable, List, Sequence, Set, Tuple

Symbol = str
Production = Tuple[Symbol, ...]

EPSILON = "ε"


def make_production(*symbols: Symbol) -> Production:
    return tuple(symbols)


def first_of_sequence(
    sequence: Sequence[Symbol],
    first_sets: Dict[Symbol, Set[Symbol]],
    non_terminals: Set[Symbol],
) -> Set[Symbol]:
    result: Set[Symbol] = set()
    if not sequence:
        result.add(EPSILON)
        return result

    for symbol in sequence:
        if symbol in non_terminals:
            result.update(first_sets[symbol] - {EPSILON})
            if EPSILON in first_sets[symbol]:
                continue
            break
        else:
            result.add(symbol)
            break
    else:
        result.add(EPSILON)
    return result


def build_grammar() -> OrderedDict[Symbol, List[Production]]:
    g: OrderedDict[Symbol, List[Production]] = OrderedDict()

    def add(lhs: Symbol, productions: Iterable[Production]) -> None:
        g[lhs] = list(productions)

    add("Modulo", [make_production("Item", "Modulo"), make_production()])
    add("Item", [make_production("Funcao"), make_production("VariavelGlobal")])

    add(
        "Funcao",
        [
            make_production(
                "functio",
                "Identificador",
                "FuncaoGenericosOpt",
                "(",
                "ParametrosOpt",
                ")",
                "FuncaoTipoRetOpt",
                "Bloco",
            )
        ],
    )
    add("FuncaoGenericosOpt", [make_production("Genericos"), make_production()])
    add("ParametrosOpt", [make_production("ListaParametros"), make_production()])
    add("FuncaoTipoRetOpt", [make_production("->", "Tipo"), make_production()])
    add("Genericos", [make_production("<", "ListaIdent", ">")])
    add("ListaIdent", [make_production("Identificador", "ListaIdentTail")])
    add(
        "ListaIdentTail",
        [make_production(",", "Identificador", "ListaIdentTail"), make_production()],
    )
    add("ListaParametros", [make_production("Parametro", "ListaParametrosTail")])
    add(
        "ListaParametrosTail",
        [make_production(",", "Parametro", "ListaParametrosTail"), make_production()],
    )
    add("Parametro", [make_production("Identificador", "ParametroTipoOpt")])
    add("ParametroTipoOpt", [make_production(":", "Tipo"), make_production()])
    add(
        "VariavelGlobal",
        [
            make_production(
                "VarGlobalPrefix",
                "Identificador",
                "VarGlobalTipoOpt",
                "VarGlobalInitOpt",
                ";",
            )
        ],
    )
    add("VarGlobalPrefix", [make_production("mutabilis"), make_production("constans")])
    add("VarGlobalTipoOpt", [make_production(":", "Tipo"), make_production()])
    add("VarGlobalInitOpt", [make_production("=", "Expressao"), make_production()])

    add("Bloco", [make_production("{", "BlocoConteudoOpt", "}")])
    add(
        "BlocoConteudoOpt",
        [make_production("Declaracao", "BlocoConteudoOpt"), make_production()],
    )
    add("Declaracao", [make_production("VariavelLocal"), make_production("Instrucao")])
    add(
        "VariavelLocal",
        [
            make_production(
                "VarLocalPrefix",
                "Identificador",
                "VarLocalTipoOpt",
                "VarLocalInitOpt",
                ";",
            )
        ],
    )
    add("VarLocalPrefix", [make_production("mutabilis"), make_production("constans")])
    add("VarLocalTipoOpt", [make_production(":", "Tipo"), make_production()])
    add("VarLocalInitOpt", [make_production("=", "Expressao"), make_production()])

    add(
        "Instrucao",
        [
            make_production("ExprInstrucao"),
            make_production("Retorno"),
            make_production("IfInstrucao"),
            make_production("WhileInstrucao"),
            make_production("ForInstrucao"),
            make_production("Bloco"),
            make_production("frange", ";"),
            make_production("perge", ";"),
        ],
    )
    add("ExprInstrucao", [make_production("Expressao", ";")])
    add("Retorno", [make_production("redde", "RetornoExprOpt", ";")])
    add("RetornoExprOpt", [make_production("Expressao"), make_production()])
    add("IfInstrucao", [make_production("si", "Expressao", "Instrucao", "IfElseOpt")])
    add("IfElseOpt", [make_production("aliter", "Instrucao"), make_production()])
    add("WhileInstrucao", [make_production("dum", "Expressao", "Instrucao")])
    add(
        "ForInstrucao",
        [make_production("pro", "Identificador", "in", "Expressao", "Instrucao")],
    )

    add("Expressao", [make_production("Atribuicao")])
    add("Atribuicao", [make_production("Ternario", "AtribuicaoOpt")])
    add("AtribuicaoOpt", [make_production("=", "Atribuicao"), make_production()])

    add("Ternario", [make_production("Coalescencia", "TernarioOpt")])
    add(
        "TernarioOpt",
        [make_production("?", "Expressao", ":", "Expressao"), make_production()],
    )

    add("Coalescencia", [make_production("LogicoOu", "CoalescenciaTail")])
    add(
        "CoalescenciaTail",
        [make_production("??", "LogicoOu", "CoalescenciaTail"), make_production()],
    )

    add("LogicoOu", [make_production("LogicoE", "LogicoOuTail")])
    add(
        "LogicoOuTail",
        [make_production("||", "LogicoE", "LogicoOuTail"), make_production()],
    )

    add("LogicoE", [make_production("Igualdade", "LogicoETail")])
    add(
        "LogicoETail",
        [make_production("&&", "Igualdade", "LogicoETail"), make_production()],
    )

    add("Igualdade", [make_production("Comparacao", "IgualdadeTail")])
    add(
        "IgualdadeTail",
        [
            make_production("IgualdadeOp", "Comparacao", "IgualdadeTail"),
            make_production(),
        ],
    )
    add(
        "IgualdadeOp",
        [
            make_production("=="),
            make_production("!="),
            make_production("==="),
            make_production("!=="),
        ],
    )

    add("Comparacao", [make_production("Soma", "ComparacaoTail")])
    add(
        "ComparacaoTail",
        [make_production("CompOp", "Soma", "ComparacaoTail"), make_production()],
    )
    add(
        "CompOp",
        [
            make_production(">"),
            make_production(">="),
            make_production("<"),
            make_production("<="),
        ],
    )

    add("Soma", [make_production("Produto", "SomaTail")])
    add(
        "SomaTail",
        [make_production("SomaOp", "Produto", "SomaTail"), make_production()],
    )
    add("SomaOp", [make_production("+"), make_production("-")])

    add("Produto", [make_production("Potencia", "ProdutoTail")])
    add(
        "ProdutoTail",
        [make_production("ProdOp", "Potencia", "ProdutoTail"), make_production()],
    )
    add("ProdOp", [make_production("*"), make_production("/"), make_production("%")])

    add("Potencia", [make_production("Unario", "PotenciaOpt")])
    add("PotenciaOpt", [make_production("**", "Potencia"), make_production()])

    add(
        "Unario",
        [make_production("UnarioOp", "Unario"), make_production("Posfixo")],
    )
    add("UnarioOp", [make_production("+"), make_production("-"), make_production("!")])

    add("Posfixo", [make_production("Primario", "PosfixoTail")])
    add(
        "PosfixoTail",
        [make_production("PosfixoSufixo", "PosfixoTail"), make_production()],
    )
    add(
        "PosfixoSufixo",
        [
            make_production("Chamado"),
            make_production("Indexacao"),
            make_production("Acesso"),
        ],
    )

    add("Chamado", [make_production("(", "ArgumentosOpt", ")")])
    add("ArgumentosOpt", [make_production("ListaArgumentos"), make_production()])
    add("Indexacao", [make_production("[", "Expressao", "]")])
    add("Acesso", [make_production(".", "Identificador")])

    add(
        "Primario",
        [
            make_production("Literal"),
            make_production("Identificador"),
            make_production("(", "Expressao", ")"),
            make_production("[", "ArgumentosOpt", "]"),
            make_production("Objeto"),
            make_production("Lambda"),
        ],
    )

    add("ListaArgumentos", [make_production("Expressao", "ListaArgumentosTail")])
    add(
        "ListaArgumentosTail",
        [make_production(",", "Expressao", "ListaArgumentosTail"), make_production()],
    )

    add("Objeto", [make_production("structura", "{", "ObjetoCamposOpt", "}")])
    add(
        "ObjetoCamposOpt",
        [make_production("CampoObjeto", "ObjetoCamposTail"), make_production()],
    )
    add(
        "ObjetoCamposTail",
        [make_production(",", "CampoObjeto", "ObjetoCamposTail"), make_production()],
    )
    add("CampoObjeto", [make_production("Identificador", ":", "Expressao")])

    add(
        "Lambda",
        [
            make_production(
                "functio",
                "LambdaGenericosOpt",
                "(",
                "ParametrosOpt",
                ")",
                "LambdaRetOpt",
                "LambdaCorpo",
            )
        ],
    )
    add("LambdaGenericosOpt", [make_production("Genericos"), make_production()])
    add("LambdaRetOpt", [make_production("->", "Tipo"), make_production()])
    add(
        "LambdaCorpo",
        [make_production("=>", "Expressao"), make_production("Bloco")],
    )

    add(
        "Literal",
        [
            make_production("Numero"),
            make_production("Texto"),
            make_production("Booleano"),
            make_production("nullum"),
            make_production("indefinitum"),
        ],
    )
    add("Booleano", [make_production("verum"), make_production("falsum")])

    add("Tipo", [make_production("TipoSimples", "TipoPosOpt")])
    add(
        "TipoPosOpt",
        [make_production("?"), make_production("SufixoTipo"), make_production()],
    )
    add(
        "TipoSimples",
        [
            make_production("Identificador"),
            make_production("[", "Tipo", "]"),
            make_production("{", "TipoCamposOpt", "}"),
            make_production("functio", "(", "ListaTiposOpt", ")", "->", "Tipo"),
        ],
    )
    add(
        "TipoCamposOpt",
        [make_production("CampoTipo", "TipoCamposTail"), make_production()],
    )
    add(
        "TipoCamposTail",
        [make_production(",", "CampoTipo", "TipoCamposTail"), make_production()],
    )
    add("CampoTipo", [make_production("Identificador", ":", "Tipo")])

    add("ListaTiposOpt", [make_production("ListaTipos"), make_production()])
    add("ListaTipos", [make_production("Tipo", "ListaTiposTail")])
    add(
        "ListaTiposTail",
        [make_production(",", "Tipo", "ListaTiposTail"), make_production()],
    )

    add("SufixoTipo", [make_production("[", "]")])

    return g


def compute_first_follow(
    grammar: OrderedDict[Symbol, List[Production]]
) -> Tuple[Dict[Symbol, Set[Symbol]], Dict[Symbol, Set[Symbol]]]:
    non_terminals = set(grammar.keys())
    first_sets: Dict[Symbol, Set[Symbol]] = {nt: set() for nt in non_terminals}
    follow_sets: Dict[Symbol, Set[Symbol]] = {nt: set() for nt in non_terminals}

    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                if not production:
                    if EPSILON not in first_sets[lhs]:
                        first_sets[lhs].add(EPSILON)
                        changed = True
                    continue
                add_epsilon = True
                for symbol in production:
                    if symbol in non_terminals:
                        additions = first_sets[symbol] - {EPSILON}
                        if not additions.issubset(first_sets[lhs]):
                            first_sets[lhs].update(additions)
                            changed = True
                        if EPSILON in first_sets[symbol]:
                            continue
                        add_epsilon = False
                        break
                    else:
                        if symbol not in first_sets[lhs]:
                            first_sets[lhs].add(symbol)
                            changed = True
                        add_epsilon = False
                        break
                if add_epsilon:
                    if EPSILON not in first_sets[lhs]:
                        first_sets[lhs].add(EPSILON)
                        changed = True

    start_symbol = next(iter(grammar))
    follow_sets[start_symbol].add("$")

    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                for index, symbol in enumerate(production):
                    if symbol not in non_terminals:
                        continue
                    beta = production[index + 1 :]
                    first_beta = first_of_sequence(beta, first_sets, non_terminals)
                    before = len(follow_sets[symbol])
                    follow_sets[symbol].update(first_beta - {EPSILON})
                    if len(follow_sets[symbol]) > before:
                        changed = True
                    if EPSILON in first_beta:
                        before = len(follow_sets[symbol])
                        follow_sets[symbol].update(follow_sets[lhs])
                        if len(follow_sets[symbol]) > before:
                            changed = True

    return first_sets, follow_sets


def build_conflict_summary(
    grammar: OrderedDict[Symbol, List[Production]],
    first_sets: Dict[Symbol, Set[Symbol]],
    follow_sets: Dict[Symbol, Set[Symbol]],
) -> Dict[str, Set[Symbol]]:
    non_terminals = set(grammar.keys())
    parse_table: Dict[Symbol, Dict[Symbol, Tuple[int, Production]]] = defaultdict(dict)
    conflicts: Dict[str, Set[Symbol]] = defaultdict(set)

    for lhs, productions in grammar.items():
        for index, production in enumerate(productions):
            first_prod = first_of_sequence(production, first_sets, non_terminals)
            for terminal in first_prod - {EPSILON}:
                if terminal in parse_table[lhs]:
                    conflicts[lhs].add(terminal)
                else:
                    parse_table[lhs][terminal] = (index, production)
            if EPSILON in first_prod:
                for terminal in follow_sets[lhs]:
                    existing = parse_table[lhs].get(terminal)
                    if existing is not None and existing[0] != index:
                        conflicts[lhs].add(terminal)
                    else:
                        parse_table[lhs][terminal] = (index, production)

    return conflicts


def format_bnf(grammar: OrderedDict[Symbol, List[Production]]) -> str:
    lines: List[str] = []
    for lhs, productions in grammar.items():
        rhs_options: List[str] = []
        for production in productions:
            if not production:
                rhs_options.append(EPSILON)
            else:
                rhs_options.append(" ".join(production))
        lines.append(f"{lhs} -> {' | '.join(rhs_options)}")
    return "\n".join(lines)


def format_table(
    grammar: OrderedDict[Symbol, List[Production]],
    first_sets: Dict[Symbol, Set[Symbol]],
    follow_sets: Dict[Symbol, Set[Symbol]],
) -> str:
    rows = ["| Não-terminal | FIRST | FOLLOW |", "| --- | --- | --- |"]
    for lhs in grammar.keys():
        first_values = sorted(first_sets[lhs], key=lambda x: (x != EPSILON, x))
        follow_values = sorted(follow_sets[lhs])
        first_display = ", ".join(first_values)
        follow_display = ", ".join(follow_values)
        rows.append(f"| `{lhs}` | {first_display} | {follow_display} |")
    return "\n".join(rows)


def format_ll1_section(conflicts: Dict[str, Set[Symbol]]) -> str:
    if not conflicts:
        return (
            "Nenhum conflito LL(1) foi encontrado; a gramática satisfaz o critério LL(1)."
        )

    lines: List[str] = [
        "A construção da tabela LL(1) apresenta conflitos porque algumas produções "
        "que geram ε compartilham lookaheads com alternativas não vazias:",
        "",
    ]
    for lhs, terminals in sorted(conflicts.items()):
        terminals_display = ", ".join(sorted(terminals))
        lines.append(f"- `{lhs}`: lookahead(s) {terminals_display}")
    lines.append("")
    lines.append(
        "Os conflitos concentram-se nos não-terminais em forma de sufixo (`*Tail`, "
        "`*Opt`), responsáveis por operadores encadeados. O mesmo token que inicia a "
        "produção recursiva também pertence ao FOLLOW do não-terminal, gerando "
        "colisões ao preencher a tabela LL(1)."
    )
    lines.append(
        "Conclusão: a gramática **não** é LL(1) e exige um parser com mais lookahead "
        "ou uma abordagem diferente (por exemplo, Pratt parser) para tratar as "
        "expressões com precedência."
    )
    return "\n".join(lines)


def main() -> None:
    grammar = build_grammar()
    first_sets, follow_sets = compute_first_follow(grammar)
    conflicts = build_conflict_summary(grammar, first_sets, follow_sets)

    bnf_block = format_bnf(grammar)
    table_block = format_table(grammar, first_sets, follow_sets)
    ll1_section = format_ll1_section(conflicts)

    doc_lines = [
        "# FIRST/FOLLOW da gramática Scriptum\n",
        "\n",
        "## Gramática (BNF)\n",
        "```bnf\n",
        bnf_block,
        "\n```\n",
        "\n",
        "## Conjuntos FIRST e FOLLOW\n",
        table_block,
        "\n\n",
        "## A gramática é LL(1)?\n",
        "\n",
        ll1_section,
        "\n",
    ]

    output_path = "docs/wiki/dev_logs/etapa_first_follow_ll1.md"
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.writelines(doc_lines)

    print(f"Documento gerado em {output_path}")


if __name__ == "__main__":
    main()
