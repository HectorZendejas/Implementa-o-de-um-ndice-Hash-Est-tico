import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# --------------------------
# Modelos de dados
# --------------------------

class Page:
    def __init__(self, page_id: int, records: list[str]):
        self.page_id = page_id
        self.records = records

class BucketNode:
    """Um 'bloco' de bucket. Se lotar (FR), encadeia para overflow."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: list[tuple[str, int]] = []  # (key, page_id)
        self.next: "BucketNode | None" = None

    def insert(self, key: str, page_id: int) -> bool:
        """Retorna True se inseriu em overflow (ou precisou criar overflow)."""
        node = self
        while True:
            if len(node.items) < node.capacity:
                node.items.append((key, page_id))
                return node is not self  # True se inseriu em overflow (não no primário)
            if node.next is None:
                node.next = BucketNode(self.capacity)
                node = node.next
            else:
                node = node.next

    def find(self, key: str) -> int | None:
        node = self
        while node is not None:
            for k, pid in node.items:
                if k == key:
                    return pid
            node = node.next
        return None

class HashIndex:
    def __init__(self, fr: int):
        self.fr = fr
        self.nb = 0
        self.buckets: list[BucketNode] = []

        # estatísticas
        self.inserts = 0
        self.collision_inserts = 0
        self.overflow_inserts = 0

    @staticmethod
    def hash_fn(key: str, nb: int) -> int:
        # hash simples e estável: h = h*31 + ord(ch)
        h = 0
        for ch in key:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return h % nb

    def build(self, pages: list[Page]):
        nr = sum(len(p.records) for p in pages)

        # NB > NR/FR
        self.nb = math.ceil(nr / self.fr) + 1
        self.buckets = [BucketNode(self.fr) for _ in range(self.nb)]

        self.inserts = 0
        self.collision_inserts = 0
        self.overflow_inserts = 0

        for page in pages:
            for key in page.records:
                b = self.hash_fn(key, self.nb)
                primary = self.buckets[b]

                # colisão: bucket primário já tinha algo
                if len(primary.items) > 0:
                    self.collision_inserts += 1

                went_overflow = primary.insert(key, page.page_id)
                if went_overflow:
                    self.overflow_inserts += 1

                self.inserts += 1

    def find_page(self, key: str) -> int | None:
        if not self.buckets:
            return None
        b = self.hash_fn(key, self.nb)
        return self.buckets[b].find(key)

    def collision_rate(self) -> float:
        return (self.collision_inserts / self.inserts * 100.0) if self.inserts else 0.0

    def overflow_rate(self) -> float:
        return (self.overflow_inserts / self.inserts * 100.0) if self.inserts else 0.0


# --------------------------
# Funções utilitárias
# --------------------------

def load_words_txt(path: str) -> list[str]:
    words = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w:
                words.append(w)
    return words

def make_pages(words: list[str], page_size: int) -> list[Page]:
    pages = []
    page_id = 0
    for i in range(0, len(words), page_size):
        chunk = words[i:i+page_size]
        pages.append(Page(page_id, chunk))
        page_id += 1
    return pages

def table_scan(pages: list[Page], key: str) -> tuple[int | None, int]:
    """Retorna (page_id_encontrada_ou_None, custo_paginas_lidas)."""
    cost = 0
    for p in pages:
        cost += 1
        if key in p.records:
            return p.page_id, cost
    return None, cost


# --------------------------
# Interface (Tkinter)
# --------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Índice Hash Estático (Python)")

        self.pages: list[Page] = []
        self.index = HashIndex(fr=8)  # FR definido pela equipe

        # --- UI ---
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Entradas
        ttk.Label(frm, text="Tamanho da página (registros):").grid(row=0, column=0, sticky="w")
        self.page_size_var = tk.StringVar(value="100")
        ttk.Entry(frm, textvariable=self.page_size_var, width=10).grid(row=0, column=1, sticky="w")

        ttk.Button(frm, text="Carregar e Construir Índice", command=self.on_build).grid(row=0, column=2, padx=10)

        ttk.Separator(frm).grid(row=1, column=0, columnspan=3, sticky="ew", pady=8)

        ttk.Label(frm, text="Chave de busca:").grid(row=2, column=0, sticky="w")
        self.key_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.key_var, width=30).grid(row=2, column=1, sticky="w")

        ttk.Button(frm, text="Buscar com Índice", command=self.on_search).grid(row=2, column=2, padx=10)

        self.scan_btn = ttk.Button(frm, text="Table Scan", command=self.on_scan, state="disabled")
        self.scan_btn.grid(row=3, column=2, padx=10, pady=(6, 0))

        # Saída
        self.out = tk.Text(frm, height=22, width=90)
        self.out.grid(row=4, column=0, columnspan=3, pady=10, sticky="nsew")
        frm.rowconfigure(4, weight=1)
        frm.columnconfigure(1, weight=1)

    def log(self, s: str):
        self.out.insert("end", s + "\n")
        self.out.see("end")

    def _resolve_data_path(self) -> str | None:
        """
        Encontra o arquivo de palavras de forma robusta:
        - primeiro tenta na mesma pasta do Hash.py
        - depois tenta nas subpastas comuns do zip (english-words-master/...)
        """
        base_dir = Path(__file__).resolve().parent

        candidates = [
            base_dir / "words_alpha.txt",
            base_dir / "english-words.txt",
            base_dir / "english_words.txt",
            base_dir / "english-words-master" / "words_alpha.txt",
            base_dir / "english-words-master" / "english-words-master" / "words_alpha.txt",
        ]

        for p in candidates:
            if p.exists():
                return str(p)

        return None

    def on_build(self):
        try:
            page_size = int(self.page_size_var.get())
            if page_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Tamanho da página deve ser um inteiro > 0.")
            return

        # 1) localizar arquivo
        data_path = self._resolve_data_path()
        if data_path is None:
            base_dir = Path(__file__).resolve().parent
            messagebox.showerror(
                "Arquivo não encontrado",
                "Não achei o arquivo .txt com as palavras.\n\n"
                "Coloque 'words_alpha.txt' na mesma pasta do Hash.py\n"
                "OU mantenha dentro de english-words-master/...\n\n"
                f"Pasta do projeto:\n{base_dir}"
            )
            return

        # 2) carregar arquivo
        self.out.delete("1.0", "end")
        self.log("Carregando arquivo de palavras...")
        self.log(f"Arquivo usado: {data_path}")
        words = load_words_txt(data_path)
        self.log(f"NR (nº de registros): {len(words)}")

        # 3) dividir em páginas
        self.pages = make_pages(words, page_size)
        self.log(f"Quantidade de páginas: {len(self.pages)}")

        # 4) construir índice
        self.log("Construindo índice hash...")
        self.index.build(self.pages)

        self.log(f"FR (capacidade do bucket): {self.index.fr}")
        self.log(f"NB (nº de buckets): {self.index.nb}")

        # 5) mostrar primeira e última página
        first = self.pages[0]
        last = self.pages[-1]
        self.log("\n--- Primeira página ---")
        self.log(f"Página {first.page_id}: {first.records[:20]}{' ...' if len(first.records) > 20 else ''}")
        self.log("\n--- Última página ---")
        self.log(f"Página {last.page_id}: {last.records[:20]}{' ...' if len(last.records) > 20 else ''}")

        # 6) estatísticas
        self.log("\n--- Estatísticas ---")
        self.log(f"Taxa de colisões: {self.index.collision_rate():.2f}%")
        self.log(f"Taxa de overflows: {self.index.overflow_rate():.2f}%")

        self.scan_btn.config(state="normal")

    def on_search(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning("Atenção", "Digite uma chave para buscar.")
            return
        if not self.pages:
            messagebox.showwarning("Atenção", "Construa o índice primeiro.")
            return

        t0 = time.perf_counter()
        page_id = self.index.find_page(key)
        t1 = time.perf_counter()

        # custo (páginas lidas) na busca por índice:
        # se encontrou, 1 página lida; se não encontrou, 0
        cost = 1 if page_id is not None else 0

        self.log("\n=== Busca com índice ===")
        if page_id is None:
            self.log(f"Chave '{key}' NÃO encontrada. Custo: {cost} páginas lidas. Tempo: {(t1-t0)*1000:.3f} ms")
        else:
            self.log(f"Chave '{key}' encontrada na Página {page_id}. Custo: {cost} página lida. Tempo: {(t1-t0)*1000:.3f} ms")

    def on_scan(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning("Atenção", "Digite uma chave para buscar.")
            return
        if not self.pages:
            messagebox.showwarning("Atenção", "Construa o índice primeiro.")
            return

        t0 = time.perf_counter()
        page_id, cost = table_scan(self.pages, key)
        t1 = time.perf_counter()

        self.log("\n=== Table Scan ===")
        if page_id is None:
            self.log(f"Chave '{key}' NÃO encontrada. Custo: {cost} páginas lidas. Tempo: {(t1-t0)*1000:.3f} ms")
        else:
            self.log(f"Chave '{key}' encontrada na Página {page_id}. Custo: {cost} páginas lidas. Tempo: {(t1-t0)*1000:.3f} ms")


if __name__ == "__main__":
    App().mainloop()