# Implementa-o-de-um-ndice-Hash-Est-tico
Simulador de Índice Hash Estático com Análise de Custo de Busca

Este projeto consiste na implementação de um índice hash estático com interface gráfica, simulando o funcionamento de um mecanismo de indexação utilizado em sistemas de gerenciamento de banco de dados.

O sistema realiza a carga de um arquivo contendo aproximadamente 370 mil palavras do idioma inglês, organizando os registros em páginas de tamanho configurável pelo usuário. A partir dessas páginas, é construído um índice hash que associa cada chave de busca ao endereço da página onde o registro está armazenado.

A implementação contempla:

Estrutura de páginas simulando organização física em disco;

Estrutura de buckets com capacidade limitada;

Função hash própria para mapeamento das chaves;

Tratamento de colisões;

Tratamento de overflow por encadeamento;

Cálculo da taxa de colisões e overflows;

Estimativa de custo baseada na quantidade de páginas lidas;

Comparação de desempenho entre busca utilizando índice e busca sequencial (table scan).

O sistema permite demonstrar, de forma prática, a diferença de eficiência entre um mecanismo indexado e uma varredura completa da tabela, evidenciando a redução significativa de custo e tempo de acesso proporcionada pelo uso de índices hash.
