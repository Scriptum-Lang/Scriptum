## Definição Formal do Alfabeto da Linguagem Scriptum

$\Sigma_{scriptum} = \Sigma_{letras}  \cup \Sigma_{digitos} \cup \Sigma_{acentos} \cup \Sigma_{operadores} \cup \Sigma_{delimitadores} \cup \Sigma_{especiais}$ 
onde:
$\Sigma_{letrasmin} = \lbrace a,b,c,...,z \rbrace$ (26 símbolos)
$\Sigma_{letrasmai} = \lbrace A,B,C,...,Z \rbrace$ (26 símbolos)
$\Sigma_{digitos} = \lbrace 0,1,2,3,4,5,6,7,8,9 \rbrace$ (10 símbolos)
$\Sigma_{operadores} = \lbrace +, -, *, /, =, <, >, !, \And, |, \textasciicircum , \%, ?   \rbrace$ 
$\Sigma_{delimitadores} = \lbrace (,),\lbrace,\rbrace,[,],;,:,.,,,\textquotedblright \rbrace$
$\Sigma_{especiais} = \lbrace espaço,tab, newline, underscore \rbrace$

## Especificações de Tokens
### Identificadores (snake_case obrigatório)
$Identificadores = (Letrasmin) \cdot (Letrasmin \cup Digitos \cup \lbrace \_ \rbrace)^*$

### Palavras-chave (CamelCase obrigatório)
$PalavrasChave = (si, aliter, per, dum, classis, publicus, ...)$

### Literais Numéricos
$$Inteiros = Digitos^+$$
$$Decimais = Digitos^+ \cdot \lbrace.\rbrace \cdot Digitos^+$$
$$NumerosValidos = Inteiros \cup Decimais$$
### Comentários usando Fechamento de Kleene
$$ComentariosLinha = \lbrace // \rbrace \cdot (\Sigma_{scriptum}- \lbrace newline \rbrace)^* \cdot \lbrace newline \rbrace$$
$$ComentariosBlocos = \lbrace /* \rbrace \cdot (\Sigma_{scriptum})^* \cdot \lbrace */ \rbrace$$
## Exemplo na Linguagem Scriptum
```scriptum
INTEGER PRINCIPAL()
INITIUM
	INTEGER numerus, i;
	IMPRIME("Digite um número: " + i);
	LEGERE(numerus);
	
	SI (numerus > 0 ET numerus <= 10)
	INITIUM
		PRO(i EST 1; i <= 10; i++)
		INITIUM
			IMPRIME(numerus + " X " + i + " = " + numerus * i);
		FINIS PRO;
		REDDE: 0;
	FINIS SI;
	ALITER
	INITIUM
		IMPRIME("ERROR");
		REDDE 1;
	FINIS ALITER;
FINIS PRINCIPAL;


```