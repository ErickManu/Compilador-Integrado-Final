"""Interfaz de Compilador Integrado, solo biblioteca estándar de Python."""
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from pprint import pformat
from pipeline import CompilationError, compile_source, export_browser, stage_report

ROOT = Path(__file__).resolve().parent
EXAMPLE = (ROOT / 'ejemplos' / 'demo.java').read_text(encoding='utf-8')


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('Compilador Integrado | Java simplificado → JavaScript')
        root.geometry('1150x770')
        root.minsize(820, 550)
        self.result = None
        self.folder = None
        self.backend = tk.StringVar(value='auto')

        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'), foreground='#164b86')
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'), foreground='#164b86')

        main = ttk.Frame(root, padding=16)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='Compilador Integrado', style='Title.TLabel').pack(anchor='w')
        ttk.Label(main, text='Léxico → Sintáctico → Semántico → Código intermedio → JavaScript → Navegador').pack(anchor='w', pady=(1, 12))
        bar = ttk.Frame(main)
        bar.pack(fill='x', pady=(0, 10))
        ttk.Label(bar, text='Analizador léxico:').pack(side='left', padx=(0, 5))
        ttk.Combobox(bar, values=('auto', 'flex', 'python'), width=10,
                     textvariable=self.backend, state='readonly').pack(side='left', padx=(0, 12))
        ttk.Button(bar, text='1. Analizar y traducir', command=self.compile).pack(side='left', padx=4)
        ttk.Button(bar, text='2. Guardar JS + HTML', command=self.save).pack(side='left', padx=4)
        ttk.Button(bar, text='3. Abrir navegador', command=self.open_browser).pack(side='left', padx=4)
        ttk.Button(bar, text='Cargar ejemplo', command=self.load_example).pack(side='right', padx=4)
        ttk.Button(bar, text='Limpiar', command=self.clear).pack(side='right', padx=4)

        editor = ttk.PanedWindow(main, orient='horizontal')
        editor.pack(fill='both', expand=True)
        left = ttk.Frame(editor)
        right = ttk.Frame(editor)
        editor.add(left, weight=1)
        editor.add(right, weight=1)
        ttk.Label(left, text='Código fuente (Java simplificado)', style='Heading.TLabel').pack(anchor='w', pady=(0, 5))
        self.source = tk.Text(left, font=('Consolas', 11), wrap='none', undo=True,
                              background='#fff', foreground='#193550', height=20)
        self.source.pack(fill='both', expand=True, padx=(0, 8))
        self.source.insert('1.0', EXAMPLE)
        self.source.bind('<<Modified>>', self._source_edited)
        ttk.Label(right, text='Código traducido (JavaScript)', style='Heading.TLabel').pack(anchor='w', pady=(0, 5))
        self.output = tk.Text(right, font=('Consolas', 11), wrap='none', state='disabled',
                              background='#f5faff', foreground='#193550', height=20)
        self.output.pack(fill='both', expand=True)

        tabs = ttk.Notebook(main)
        tabs.pack(fill='both', expand=False, pady=(12, 0))
        tok_tab, sym_tab, log_tab = ttk.Frame(tabs), ttk.Frame(tabs), ttk.Frame(tabs)
        tabs.add(log_tab, text='Estado y errores')
        tabs.add(tok_tab, text='Tokens')
        tabs.add(sym_tab, text='Tabla de símbolos')
        ast_tab, ir_tab = ttk.Frame(tabs), ttk.Frame(tabs)
        tabs.add(ast_tab, text='AST sintáctico')
        tabs.add(ir_tab, text='Código intermedio')
        self.log = tk.Text(log_tab, height=7, font=('Consolas', 10), wrap='word', state='disabled')
        self.log.pack(fill='both', expand=True, padx=6, pady=6)
        self.tokens = self.make_tree(tok_tab, ('tipo', 'valor', 'línea', 'columna'))
        self.symbols = self.make_tree(sym_tab, ('nombre', 'tipo', 'línea', 'ámbito'))
        self.ast = self.make_text(ast_tab)
        self.intermediate = self.make_text(ir_tab)
        self.status = tk.StringVar(value='Escribe el código y pulsa «Analizar y traducir».')
        ttk.Label(main, textvariable=self.status, foreground='#184a7a').pack(anchor='w', pady=(8, 0))
        root.bind('<Control-Return>', lambda _: self.compile())

    @staticmethod
    def make_text(parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=6, pady=6)
        widget = tk.Text(frame, height=7, font=('Consolas', 10), wrap='none', state='disabled')
        scroll = ttk.Scrollbar(frame, orient='vertical', command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        widget.pack(fill='both', expand=True)
        return widget

    @staticmethod
    def make_tree(parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=6)
        for col in columns:
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=120, stretch=True)
        tree.pack(fill='both', expand=True, padx=6, pady=6)
        return tree

    def _source_edited(self, event=None):
        if self.source.edit_modified():
            self.source.edit_modified(False)
            self.result = None
            self.folder = None
            self.clear_results()
            self.status.set('Código modificado: vuelve a analizar antes de guardar.')

    @staticmethod
    def set_text(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')

    def clear_trees(self):
        for tree in (self.tokens, self.symbols):
            tree.delete(*tree.get_children())

    def clear_results(self):
        self.clear_trees()
        for widget in (self.output, self.ast, self.intermediate, self.log):
            self.set_text(widget, '')

    def show_analysis(self, result):
        for token in result.tokens:
            self.tokens.insert('', 'end', values=(token.type, token.value, token.line, token.column))
        for sym in result.symbols:
            self.symbols.insert('', 'end', values=(sym.name, sym.data_type, sym.line, sym.scope))
        if result.program is not None:
            self.set_text(self.ast, pformat(result.program, width=90))

    def compile(self):
        self.result = None
        self.folder = None
        self.clear_results()
        self.source.edit_modified(False)
        code = self.source.get('1.0', 'end-1c')
        try:
            result = compile_source(code, self.backend.get())
        except CompilationError as exc:
            self.show_analysis(exc)
            self.set_text(self.log, stage_report(exc) + '\n\n' + '\n'.join(exc.problems))
            self.status.set(f'Error en la fase {exc.stage}. No se generó JavaScript.')
            return
        self.result = result
        self.show_analysis(result)
        self.set_text(self.output, result.javascript)
        self.set_text(self.intermediate, result.intermediate)
        self.set_text(self.log, stage_report(result) + '\n\n'
                      'Siguiente paso: Guardar JS + HTML y abrir en el navegador.')
        self.status.set(f'Análisis correcto. {len(result.tokens)-1} tokens; {len(result.symbols)} variables.')

    def save(self):
        if self.result is None:
            messagebox.showwarning('Analiza primero', 'Pulsa Analizar y traducir con código válido.')
            return
        selected = filedialog.askdirectory(title='Elige carpeta para guardar programa.js e index.html',
                                           initialdir=str(ROOT))
        if not selected:
            return
        try:
            js, html = export_browser(self.result, Path(selected))
        except OSError as exc:
            self.folder = None
            messagebox.showerror('No se pudo guardar', str(exc))
            return
        self.folder = html.parent
        self.status.set(f'Guardado: {js.name} y {html.name} en {self.folder}')
        messagebox.showinfo('Archivos guardados', f'{js}\n{html}\n{html.parent / "intermedio.txt"}\n\nAhora puedes abrir el navegador.')

    def open_browser(self):
        if self.result is None:
            messagebox.showwarning('Analiza primero', 'Debes analizar el código antes de ejecutarlo.')
            return
        if self.folder is None:
            messagebox.showinfo('Primero guarda', 'Pulsa «Guardar JS + HTML» para elegir una carpeta.')
            return
        webbrowser.open((self.folder / 'index.html').resolve().as_uri())
        self.status.set('Navegador abierto: la salida aparece en la página y en F12 → Console.')

    def load_example(self):
        self.clear_results()
        self.source.delete('1.0', 'end')
        self.source.insert('1.0', EXAMPLE)
        self.result = None
        self.folder = None
        self.status.set('Ejemplo cargado; pulsa Analizar y traducir.')

    def clear(self):
        self.source.delete('1.0', 'end')
        self.clear_results()
        self.result = None
        self.folder = None
        self.status.set('Editor limpio.')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--self-test':
        from smoke_check import main as smoke_main
        raise SystemExit(smoke_main(sys.argv[2:]))
    root = tk.Tk()
    App(root)
    root.mainloop()
