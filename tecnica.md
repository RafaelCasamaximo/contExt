# Tecnica do Metodo de Diferencas Finitas no ContExt

Este documento explica como o ContExt resolve problemas de `Laplace` e `Poisson` quando a malha e:

- uniforme
- adaptativa
- esparsa

O foco aqui e o que o software faz hoje no codigo, nao uma formulacao generica qualquer.

## 1. Problema resolvido

O solver trabalha com problemas elipticos escalares 2D com condicoes de contorno de `Dirichlet`.

Os dois casos disponiveis na interface sao:

- `Laplace`: sem termo fonte
- `Poisson`: com termo fonte constante

No codigo, a forma discreta montada segue a convencao:

`-∇²u = f`

Por isso, quando a fronteira e zero e `f > 0`, a solucao tende a ficar positiva no interior.

Hoje, o solver aceita:

- valores de Dirichlet por subcontorno
- termo fonte escalar constante para Poisson

Hoje, o solver nao implementa:

- Neumann
- Robin
- termo fonte espacial `f(x, y)` arbitrario

## 2. Fluxo geral no projeto

O fluxo numerico foi organizado em dois niveis:

- `src/context/core/_mesh.py` e `src/context/core/_sparseMesh.py`
  - geram o contorno discretizado e os eixos da malha
- `src/context/core/_fdm.py`
  - constroi o dominio discreto
  - monta o sistema linear
  - resolve o problema
- `src/context/core/_simulation.py`
  - escolhe automaticamente o modo uniforme, adaptativo ou esparso
  - aplica os valores de Dirichlet
  - executa Laplace ou Poisson

## 3. Malha uniforme

Na malha uniforme, todos os espacamentos sao constantes:

- `dx = constante`
- `dy = constante`

O dominio discreto e uma grade estruturada retangular, e cada no interno usa os quatro vizinhos cardinais:

- oeste
- leste
- sul
- norte

O stencil fica no formato classico de 5 pontos.

No sistema linear:

- a diagonal recebe a soma dos coeficientes locais
- os vizinhos entram com sinal negativo
- os valores prescritos de Dirichlet entram no lado direito

Esse caso continua existindo como caso particular do solver geral.

## 4. Malha adaptativa

### 4.1. Como a malha e representada

Na malha adaptativa, a grade ainda e estruturada, mas os espacamentos deixam de ser constantes.

Em vez de um unico `dx` e `dy`, o solver usa:

- `x_coords`: coordenadas reais dos nos em `x`
- `y_coords`: coordenadas reais dos nos em `y`

Essas coordenadas vem do `SparseMesh.dx` e `SparseMesh.dy`, que guardam os intervalos reais da malha adaptativa.

Entao, cada no interno passa a ter quatro espacamentos locais:

- `h_w`: distancia ate o vizinho oeste
- `h_e`: distancia ate o vizinho leste
- `h_s`: distancia ate o vizinho sul
- `h_n`: distancia ate o vizinho norte

### 4.2. Discretizacao usada

Para cada no interno, o codigo monta os coeficientes locais:

- `a_e = 2 / (h_e * (h_e + h_w))`
- `a_w = 2 / (h_w * (h_e + h_w))`
- `a_n = 2 / (h_n * (h_n + h_s))`
- `a_s = 2 / (h_s * (h_n + h_s))`
- `a_p = a_e + a_w + a_n + a_s`

Isso gera o sistema:

`a_p * u(i,j) - a_e * u_E - a_w * u_W - a_n * u_N - a_s * u_S = f`

No caso de `Laplace`, `f = 0`.

No caso de `Poisson`, `f` e o valor constante informado na interface.

### 4.3. Efeito pratico

A malha adaptativa permite:

- manter uma grade estruturada
- usar nos mais densos em regioes de interesse
- preservar um solver unico para Laplace e Poisson

Como o dominio ainda e estruturado, o problema e resolvido diretamente em uma unica malha.

## 5. Malha esparsa

### 5.1. Por que a malha esparsa e diferente

Na malha esparsa, a ideia nao e apenas mudar o espacamento local.

Aqui o dominio e dividido em:

- uma malha grossa de fundo
- uma ou mais regioes refinadas

Isso cria uma interface entre grade grossa e grade fina. Nessa interface aparecem os chamados `hanging nodes`, ou seja, pontos da grade fina que nao possuem correspondencia 1:1 com a vizinhanca da grade grossa.

Por esse motivo, o ContExt nao resolve a malha esparsa com um unico stencil irregular global.

### 5.2. Estrategia implementada

Foi implementada a estrategia de acoplamento por subdominios, que era a `opcao 2` da discussao tecnica:

1. resolver o dominio grosso
2. usar a solucao grossa para fornecer valores de interface ao patch fino
3. resolver o patch fino
4. devolver os valores do patch fino para a interface grossa
5. repetir ate convergir

No codigo, isso aparece como um `CompositeDomain` em `_fdm.py`, com:

- `background_domain`
  - dominio grosso completo, usado para inicializar a interface
- `coarse_domain`
  - dominio grosso exterior, com “buracos” nas regioes refinadas
- `patches`
  - subdominios finos, um por regiao refinada

### 5.3. Como o acoplamento funciona

Para cada patch refinado:

1. o solver calcula uma solucao inicial no dominio grosso completo
2. os valores da borda do patch na grade grossa sao extraidos dessa solucao inicial
3. esses valores viram Dirichlet na interface do dominio grosso com buraco
4. a solucao do dominio grosso e interpolada para a borda do patch fino
5. o patch fino e resolvido com esses valores de Dirichlet na sua interface
6. a solucao fina e amostrada de volta nos nos de interface da grade grossa
7. o processo repete ate a diferenca maxima de interface ficar abaixo da tolerancia

Hoje os parametros do acoplamento sao:

- tolerancia de interface: `1e-6`
- maximo de iteracoes: `50`

Se a interface nao converge nesse limite, o solver falha em vez de retornar um resultado inconsistente.

### 5.4. Interpolacao na interface

Como a borda fina geralmente tem mais nos que a borda grossa, o codigo usa interpolacao linear ao longo das arestas retangulares do patch:

- oeste
- leste
- sul
- norte

Essa interpolacao e usada em dois sentidos:

- da malha grossa para a malha fina
- da malha fina para a malha grossa

### 5.5. Composicao da solucao final

Depois da convergencia:

- os valores da malha grossa sao usados fora dos patches
- os valores da malha fina substituem a solucao dentro dos patches

O resultado final e escrito em uma grade global de coordenadas, mas so os nos que realmente existem na malha esparsa entram como nos ativos da simulacao.

Ou seja:

- os nos fisicos do contorno continuam sendo de fronteira
- os nos de interface entre grosso e fino nao aparecem como fronteira fisica
- para estatistica e exportacao, a interface e tratada como parte interna do problema acoplado

## 6. Poisson em malha adaptativa e esparsa

O caso de `Poisson` usa exatamente a mesma infraestrutura de discretizacao e acoplamento, mudando apenas o lado direito do sistema.

### 6.1. Na malha adaptativa

Cada equacao local recebe o termo:

`f = source_term`

Como o stencil usa os espacamentos locais, a contribuicao dos vizinhos muda de no para no, mas o termo fonte continua entrando como um escalar constante no vetor do sistema.

### 6.2. Na malha esparsa

O termo fonte entra em todos os subproblemas:

- no dominio grosso completo de inicializacao
- no dominio grosso exterior
- em cada patch refinado

Assim, o caso de Poisson em malha esparsa nao e resolvido por uma aproximacao separada. Ele usa o mesmo acoplamento coarse/fine do caso de Laplace, mas com o lado direito nao nulo em todos os subdominios.

## 7. Condicoes de Dirichlet

Os valores de contorno sao definidos por subcontornos na interface do app.

Internamente:

- cada no de fronteira fisica recebe um `region_id`
- cada `region_id` recebe um valor informado pelo usuario
- esse valor e inserido diretamente como condicao de Dirichlet

No caso esparso:

- a fronteira fisica continua vindo do contorno do problema
- a interface entre malha grossa e fina tambem usa Dirichlet
- mas esses valores de interface nao vem do usuario
- eles sao atualizados iterativamente pelo proprio acoplamento numerico

## 8. Solver linear

O projeto agora monta matrizes esparsas com `SciPy`:

- montagem em `lil_matrix`
- resolucao em `csr` com `spsolve`

Isso foi necessario porque:

- malhas adaptativas aumentam o numero de nos utilmente resolviveis
- malhas esparsas exigem varios solves estruturados durante o acoplamento
- a matriz densa anterior limitava demais o tamanho pratico do problema

## 9. Resumo conceitual

Em termos simples:

- malha uniforme
  - um unico stencil classico em uma grade regular
- malha adaptativa
  - um unico dominio estruturado, mas com coeficientes locais diferentes em cada no
- malha esparsa
  - varios dominios estruturados acoplados iterativamente pela interface
- Poisson
  - mesmo processo de discretizacao, mas com termo fonte constante no lado direito

## 10. Limitacoes atuais

As limitacoes atuais mais importantes sao:

- apenas Dirichlet
- termo fonte apenas constante
- patches esparsos retangulares
- acoplamento esparso baseado em iteracao de interface

Ainda assim, a implementacao atual ja cobre o caso essencial para simulacao em:

- malha regular
- malha adaptativa
- malha esparsa com refinamento local
