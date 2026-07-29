# 2. Motor Questor Físico (LCTOCTB)
Este é o lado ESQUERDO do painel. A realidade fiscal contábil gravada no DB.

**Evitando A Grande Quebra do 'ZZ':**
Os sistemas contábeis encerram anos (Zeram a DRE) usando uma origem 'ZZ'. Se olharmos as receitas antigas, estariam 0.00.
```python
cur_q.execute('''
    SELECT CONTACTBDEB, CONTACTBCRED, SUM(VALORLCTOCTB)
    FROM LCTOCTB 
    WHERE CODIGOEMPRESA = ? 
      AND DATAINCLUSAO BETWEEN ? AND ?
      AND CODIGOORIGLCTOCTB <> 'ZZ'  # <-- O Segredo!
''')
```
*Assim garantimos que nosso Saldo em `contas_fisicas_empresa` não é corrompido ou sumido (como aconteceu no passado na base Questor).*
