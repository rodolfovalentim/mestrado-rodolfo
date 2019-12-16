Acho que vou começar falando que há benefícios para provedoras de serviços de se implementar SFC e são conhecidos. Citar os casos de uso. Com esses casos de uso, há a necessidade de implementar chains com datacenters separados por longas distâncias e posso citar esses casos. Quanto a chains inter datacenters, eu preciso dizer as considerações que precisam ser levadas em conta e os cenários possíveis. 

Agora, estabelecido que é importante considerar esse cenário eu preciso falar do problema de se fazer isso em cenários de source routing. Digo quais são as considerações que precisam ser feitas (descoberta de topologia, pensar em outras). Agora que todos os problemas foram expostos é hora de apresentar a solução. A IETF apresentou uma arquitetura de exemplo, eu parto do exemplo, explico cada elemento e suas funções. Contextualizo os elementos para funcionarem com source routing. Acaba a seção com um diagrama a arquitetura sugerida.

Posicionar funções de rede perdo do usuário para diminuir latência pode ser um caso de uso. Efficiently Embedding Service Function Chains withDynamic Virtual Network Function Placementin Geo-distributed Cloud System

Muitos definem SFC já na introdução. Serie de funções ordenadamente concatenadas.

A maioria dos papers focam na otimização do caminho e do posicionamento. Poucos se importam  com o mecanismo de encadeamento.

Importante falar que uso o Dijkstra para selecionar o menor caminho entre os 'comutadores'.

Talvez uma imagens com layers


\begin{tcolorbox}
\textbf{Notas} 
    \begin{itemize}
    \item HSFC permite diminuir o tamanho das tabelas de regras
    \item Muito tempo na implementação pode ocasionar em quebra de SLA das provedoras
    \item KeySFC é aware ou unaware. Por que quando um pacote é encaminhado à SF, se a SF modificar o cabeçalho ethernet quebra a chain. Como esse não é o funcionamento regular de um elemento de rede, talvez não seja unaware
    \item BR-INT é um SFF
    \end{itemize}
\end{tcolorbox}
