##### 1 -  Especificação completa do alfabeto da linguagem
- Alfabeto para Identificadores: Σ1={a,b,c,…,z,A,B,C,…,Z,0,1,2,…,9,_}\Sigma_1 = \{ a, b, c, \dots, z, A, B, C, \dots, Z, 0, 1, 2, \dots, 9, \_ \}Σ1​={a,b,c,…,z,A,B,C,…,Z,0,1,2,…,9,_}
	- Este alfabeto define os caracteres válidos para formar **nomes de variáveis, funções e identificadores**.
- Alfabeto para Números: Σ2​={0,1,2,3,4,5,6,7,8,9}
	- Com este alfabeto podemos representar literais numéricos inteiros e decimais.
- Alfabeto para Operadores Aritméticos e Relacionais: Σ3​={+,−,∗,/,>,<,=}
	- Esses símbolos permitem a construção de **expressões aritméticas e condicionais**.
- Alfabeto para Palavras-chave Fonéticas: Σ4​={MEIN,BEGIN,END,PRINT,ESCAN,IF,ENDE,FOR,RETURNE,ELSI}
	- Essas palavras fazem parte do vocabulário reservado da linguagem, escritas de forma fonética.
- Alfabeto para Delimitadores e Símbolos Especiais: Σ5={; , , ,:, (, ), {, }, ", '}
##### 2 - Definição formal de todos os **tipos** de tokens
Palavras-chave: (if, else, while)
Identificadores: (variáveis, funções, tipos)
Literais: (números, strings, booleanos)
Operadores: (aritméticos, lógicos, relacionais)
Delimitadores: (parênteses, chaves, ponto-e-virgula)

##### 3 - Exemplos concretos de programas válidos na linguagem

INT MEIN
BEGIN
	INT numero, i;

		PRINT: "Digite um número: " + i;
    	ESCAN: numero;

    	IF numero > 0 ENDE numero <= 10
    	BEGIN
        	FOR i IS 1; i <= 10; I++
        	BEGIN
            		PRINT: numero + "X" + i + "=" + numero * I;
        	END FOR;
    
        	RETURNE: 0;
    
   	END IF;

    	ELSI IS
    	BEGIN
        	PRINT: "ERRO";
        	RETURNE 1;
    	END ELSI;
END MEIN;