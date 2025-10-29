# Requisitos para construção do medibot

Necessidade/dor do usuário: dificuldade/demora para conseguir encontrar e marcar horário de algum médico de forma prática e rápida. 

Proposta de solução: Usar um chatbot que integre com o whatsapp, assim a pessoa pode com linguagem natural entrar em contato e marcar rapidamente uma consulta com o médico, usando somente whatsapp é prático e com o agente consegue isso rápido.

Por enquanto a localidade é somente Porto Feliz e usará somente com um médico, mas a arquitetura precisa ser genérica para facilitar a inclusão de novos médicos e consultórios no futuro.

Fluxo da conversa

O fluxo abaixo descreve as etapas que o usuário e o bot percorrem para realizar o agendamento de uma consulta médica de forma simples e eficiente.

Fluxo unificado de conversas: agendamento, consulta, reagendamento e cancelamento

Abaixo está um diagrama mermaid que representa visualmente o fluxo de conversas entre o usuário e o bot para agendamento, consulta, reagendamento e cancelamento de consultas médicas.

```mermaid
flowchart TD
    Start[Usuário inicia conversa / saudação] --> BotResp[Bot responde saudação e informa competência]
    BotResp --> Obj{Objetivo do usuário?}
    
    %% Agendamento
    Obj -->|Agendar| AG1[Usuário solicita horário para médico específico]
    AG1 --> AG2[Bot pergunta range de datas desejado]
    AG2 --> AG3[Bot consulta API de calendário do médico]
    AG3 --> AG4[Bot retorna datas/horários disponíveis e pergunta: alterar período ou escolher]
    AG4 --> AG5{Ação do usuário}
    AG5 -->|Escolher horário| AG6[Usuário escolhe data e horário]
    AG6 --> AG7["Bot pede dados (nome, email, telefone) — se não disponíveis"]
    AG7 --> AG8[Bot agenda via API com os dados coletados]
    AG8 --> AG9[Bot confirma agendamento]
    AG9 --> End[Fim do fluxo]
    AG5 -->|Alterar período| AG2

    %% Consulta / Reagendamento / Cancelamento
    Obj -->|Consultar / Reagendar / Cancelar| C1[Usuário pede consultas agendadas]
    C1 --> C2["Bot solicita identidade (nome, email ou telefone)"]
    C2 --> C3[Bot consulta API para recuperar agendamentos]
    C3 --> C4[Bot apresenta agendamentos e pergunta: cancelar, reagendar ou manter]
    C4 -->|Cancelar| C5[Bot solicita confirmação e cancela via API]
    C5 --> C6[Bot confirma cancelamento] --> End
    C4 -->|Reagendar| R1[Bot solicita novo range de datas]
    R1 --> R2[Bot consulta API por novas opções]
    R2 --> R3[Bot apresenta opções; usuário escolhe novo horário]
    R3 --> R4["Bot atualiza/agendamento via API (mantendo dados do paciente)"]
    R4 --> R5[Bot confirma reagendamento] --> End
    C4 -->|Manter| End

    %% Ações proativas
    BotResp --> PCheck[Bot verifica proativamente horários do dia / vagas abertas]
    PCheck --> PNotify[Bot notifica usuário com opções e solicita confirmação]
    PNotify -->|Usuário confirma| PBook{Tem dados do usuário?}
    PBook -->|Sim| PBook2[Bot agenda via API e confirma] --> End
    PBook -->|Não| PCollect["Bot pede dados (nome, email, telefone)"] --> PBook2

    PNotify -->|Usuário não tem interesse| End

    %% Contexto / troca de assunto
    ANY[Em qualquer ponto: usuário muda de assunto] --> SaveCtx[Bot salva contexto e responde fora do fluxo]
    SaveCtx --> Return[Bot retorna ao fluxo anterior sem encerrar a sessão]
    Return --> BotResp

    style Start fill:#e0e0e0,color:#000000
    style End fill:#c8e6c9,color:#000000
    style AG7 fill:#fff8e0,color:#000000
```

Observações rápidas:
- Nunca encerrar a sessão por troca de assunto: salvar contexto, responder e voltar ao fluxo.
- Encerrar apenas se o usuário indicar desinteresse em agendar.
- Fluxo deve ser simples e sem overengineering (MVP).
- Incluir lógica para reutilizar dados já conhecidos do usuário quando possível (evita pedir repetidamente).
- Permitir reentrada no fluxo após ações proativas.



Além dessa parte, preciso que o sistema seja ativo em buscar os horários do dia e informar o usuário via mensagem, solicitando confirmação.

Se em alguma parte do fluxo da conversa o usuário mudar de assunto do contexto o bot precisa voltar ao contexto mas não encerrar a sessão. Apenas encerrar a sessão se o usuário dar indícios de que não demonstrar interesse em agendar horário.

Não use overengineering nesse caso, visto que o sistema precisa ser um mvp, custo baixo de manutenção e inicia-se com poucos médicos/demandas.

Verifique qual framework python é mais fácil de usar para este caso (rápido de construir e tranquilo de manutenção), ou se nesse caso não precisa de framework.

