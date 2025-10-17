import linecache

# ============================================================
# Função principal que processa o arquivo de entrada
# ============================================================
def processar_entrada(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in:
        linhas = f_in.readlines()

    # Identifica o tipo de máquina
    if linhas[0].startswith(';S'):
        linhas[0] = ' Sipser\n'
    elif linhas[0].startswith(';I'):
        linhas[0] = ' Infinite\n'

    # Remove comentários
    for i in range(len(linhas)):
        if ';' in linhas[i]:
            partes = linhas[i].split(';')
            linhas[i] = partes[0].strip()

    # Salva arquivo temporário
    texto_final = '\n'.join(linhas) + '\n'
    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write(texto_final)

    # Chama a função de conversão dependendo do modelo
    if linhas[0].startswith(' Sipser'):
        converter_sipser(output_file)
    else:
        gerar_transicoes_auxiliares(input_file, output_file)

# ============================================================
# Função que extrai estados e símbolos de uma máquina dupla
# ============================================================
def extrair_estados_e_simbolos(input_file, output_file):
    estados_unicos = set()
    simbolos_tape = set()

    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        for linha in f_in:
            parts = linha.strip().split()
            if not parts or linha.startswith(';'):
                continue
            # Ajuste de estado inicial
            if parts[0] == '0':
                parts[0] = 'ini'
                if parts[-1] == '0':
                    parts[-1] = 'ini'
            f_out.write(' '.join(parts) + '\n')

            estados_unicos.add(parts[0])
            if parts[1] != '_':
                simbolos_tape.add(parts[1])

        # Adiciona linhas fixas de controle da máquina
        linhas_controle = [
            "0 0 # r passa0",
            "0 1 # r passa1",
            "passa0 0 0 r passa0",
            "passa0 1 0 r passa1",
            "passa0 _ 0 r marcaFim",
            "passa1 0 1 r passa0",
            "passa1 1 1 r passa1",
            "passa1 _ 1 r marcaFim",
            "marcaFim _ & l retornaInicio",
            "retornaInicio * * l retornaInicio",
            "retornaInicio # # r ini"
        ]
        f_out.write(';Modificações\n')
        for l in linhas_controle:
            f_out.write(l + '\n')

    return estados_unicos, simbolos_tape

# ============================================================
# Gera transições auxiliares para fita duplamente infinita
# ============================================================
def gerar_transicoes_auxiliares(input_file, output_file):
    estados_unicos, simbolos_tape = extrair_estados_e_simbolos(input_file, output_file)
    lista_estados = list(estados_unicos)
    lista_simbolos = list(simbolos_tape)

    pattern1 = "{prefix}passaHash {simbolo} _ r {prefix}passaHash{simbolo}\n"
    pattern2 = "{prefix} # # r {prefix}passaHash\n{prefix}passaHash _ _ r {prefix}passaHashBranco\n{prefix}passaHashBranco _ _ r {prefix}passaHashBranco\n"
    pattern3 = "{prefix}passaHashBranco {simbolo} _ r {prefix}passaHash{simbolo}\n"
    pattern4 = "{prefix}passaHash{simbolo} {simbolo2} {simbolo} r {prefix}passaHash{simbolo2}\n"
    pattern5 = "{prefix}passaHashBranco{simbolo} _ 0 r {prefix}\n{prefix}passaHash{simbolo} _ {simbolo} r {simbolo}volta{prefix}\n{simbolo}volta{prefix} * * l {simbolo}volta{prefix}\n{simbolo}volta{prefix} # # r {prefix}\n"

    with open(output_file, 'a', encoding='utf-8') as f_out:
        for prefix in lista_estados:
            for simbolo in lista_simbolos:
                f_out.write(pattern1.format(prefix=prefix, simbolo=simbolo))
        for prefix in lista_estados:
            f_out.write(pattern2.format(prefix=prefix))
        for prefix in lista_estados:
            for simbolo in lista_simbolos:
                f_out.write(pattern3.format(prefix=prefix, simbolo=simbolo))
        for prefix in lista_estados:
            for simbolo in lista_simbolos:
                for simbolo2 in lista_simbolos:
                    f_out.write(pattern4.format(prefix=prefix, simbolo=simbolo, simbolo2=simbolo2))
        for prefix in lista_estados:
            for simbolo in lista_simbolos:
                f_out.write(pattern5.format(prefix=prefix, simbolo=simbolo))

    # Espaço em branco final
    lista_exclusao = ['0', 'passa0', 'passa1', 'marcaFim', 'retornaInicio']
    primeiras_palavras = set()
    with open(output_file, 'r', encoding='utf-8') as f:
        for linha in f:
            if linha.startswith(';'):
                continue
            partes = linha.strip().split()
            if partes and partes[0] not in lista_exclusao:
                primeiras_palavras.add(partes[0])

    pattern6 = "{estado} & _ r espaçoDireita{estado}\nespaçoDireita{estado} _ & l {estado}\n"
    with open(output_file, 'a', encoding='utf-8') as f_out:
        for estado in primeiras_palavras:
            f_out.write(pattern6.format(estado=estado))

# ============================================================
# Converte máquina Sipser para infinita
# ============================================================
def converter_sipser(output_file):
    estados_iniciais = []
    with open(output_file, 'r+', encoding='utf-8') as f:
        linhas = f.readlines()
        for linha in linhas:
            if linha and linha[0] == '0':
                estados_iniciais.append(linha.strip())
    backup_estados = list(estados_iniciais)

    with open(output_file, 'r+', encoding='utf-8') as f:
        f.seek(0, 2)
        f.write('\n;Modificações\n')

    for i in range(len(estados_iniciais)):
        partes = estados_iniciais[i].split()
        if len(partes) >= 4:
            if partes[3] == 'r':
                partes[3] = 'l'
            partes[4] = 'ini'
            estados_iniciais[i] = ' '.join(partes)

    with open(output_file, 'r+', encoding='utf-8') as f:
        linhas = f.readlines()
        n = 0
        for i, linha in enumerate(linhas):
            if linha.startswith("0"):
                linhas[i] = estados_iniciais[n] + "\n"
                n += 1
        f.seek(0)
        f.writelines(linhas)
        f.truncate()

        f.seek(0, 2)
        f.write('ini * # r a1\n')
        estados_modificados = ['a1' + string[1:] for string in backup_estados]
        for s in estados_modificados:
            f.write(s + '\n')

    completar_transicoes_sipser(output_file)

# ============================================================
# Substitui quinta palavra se necessário
# ============================================================
def ajustar_transicoes_ini(output_file):
    linhas_mod = []
    with open(output_file, 'r+', encoding='utf-8') as f:
        for linha in f:
            if linha.startswith(';'):
                linhas_mod.append(linha)
                continue
            partes = linha.strip().split()
            if len(partes) >= 5 and partes[4] == '0':
                partes[4] = 'a1'
            linhas_mod.append(' '.join(partes) + '\n')
        f.seek(0)
        f.writelines(linhas_mod)
        f.truncate()

# ============================================================
# Finaliza máquina Sipser adicionando transições
# ============================================================
def completar_transicoes_sipser(output_file):
    vistos = set()
    with open(output_file, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    with open(output_file, 'a', encoding='utf-8') as f:
        for linha in linhas:
            if linha.startswith(';') or linha.startswith(' Sipser'):
                continue
            partes = linha.strip().split()
            if partes:
                estado = partes[0]
                if estado not in vistos:
                    vistos.add(estado)
                    f.write(f"{estado} # # r *\n")

    ajustar_transicoes_ini(output_file)

# ============================================================
# Adiciona transições faltantes para símbolos '_'
# ============================================================
def preencher_transicoes_em_branco(output_file):
    pares_existentes = set()
    simbolos = ['0', '1', '_']

    with open(output_file, 'r+', encoding='utf-8') as f:
        linhas = f.readlines()

        for linha in linhas:
            if linha.startswith(';') or not linha.strip():
                continue
            partes = linha.strip().split()
            if len(partes) >= 5:
                pares_existentes.add((partes[0], partes[1]))

        novas_transicoes = []
        for linha in linhas:
            if linha.startswith(';') or not linha.strip():
                continue
            partes = linha.strip().split()
            estado = partes[0]
            if (estado, '_') not in pares_existentes:
                novas_transicoes.append(f"{estado} _ _ r {estado}\n")
                pares_existentes.add((estado, '_'))

        f.seek(0, 2)
        if novas_transicoes:
            f.write("\n;Transições adicionadas para '_' faltantes\n")
            for t in novas_transicoes:
                f.write(t)

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    input_file = 'entrada.in'
    output_file = 'saida.out'

    processar_entrada(input_file, output_file)

    # Adiciona ponto e vírgula inicial se necessário
    with open(output_file, 'r+', encoding='utf-8') as f:
        conteudo = f.read()
        if not conteudo.startswith(';'):
            f.seek(0)
            f.write(';' + conteudo)

    # Remove linhas em branco
    with open(output_file, 'r+', encoding='utf-8') as f:
        linhas = f.readlines()
        linhas = [l for l in linhas if l.strip()]
        f.seek(0)
        f.writelines(linhas)
        f.truncate()

    # Garante que todas as transições para '_' estão presentes
    preencher_transicoes_em_branco(output_file)
