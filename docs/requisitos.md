# Requisitos para construção do medibot

Necessidade/dor do usuário: dificuldade/demora para conseguir encontrar e marcar horário de algum médico de forma prática e rápida. 

Proposta de solução: Usar um chatbot que integre com o whatsapp, assim a pessoa pode com linguagem natural entrar em contato e marcar rapidamente uma consulta com o médico, usando somente whatsapp é prático e com o agente consegue isso rápido.

Por enquanto a localidade é somente Porto Feliz e usará somente com um médico, mas precisa ser mais genérico a fim de poder incluir novos médicos e até consultórios.

Fluxo da conversa
```mermaid
flowchart TD
    A[Usuário inicia conversa/saudação] --> B[Bot responde saudação e informa competência]
    B --> C[Usuário solicita horário para médico específico]
    C --> D[Bot consulta API de calendário do médico]
    D --> E[Bot retorna datas e horários disponíveis]
    E --> F[Usuário escolhe data e horário desejado]
    F --> G[Bot pede informações do usuário (email, nome inteiro e telefone)]
    G --> H[Bot agenda horário via API com as informações coletadas]
    H --> I[Bot confirma agendamento para o usuário]
    I --> J[Fim do fluxo]
    
    style A fill:#e1f5fe
    style I fill:#c8e6c9
    style G fill:#fff3e0
```

Além dessa parte, preciso que o sistema seja ativo em buscar os horários do dia e informar o usuário via mensagem, solicitando confirmação.

Se em alguma parte do fluxo da conversa o usuário mudar de assunto do contexto o bot precisa voltar ao contexto mas não encerrar a sessão. Apenas encerrar a sessão se o usuário dar indícios de que não demonstrar interesse em agendar horário.

Não use overengineering nesse caso, visto que o sistema precisa ser um mvp, custo baixo de manutenção e inicia-se com poucos médicos/demandas.

Verifique qual framework python é mais fácil de usar para este caso (rápido de construir e tranquilo de manutenção), ou se nesse caso não precisa de framework.

