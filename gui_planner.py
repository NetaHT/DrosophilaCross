"""
GUI for Target Genotype Planner (ROLE-BASED)

Key model update:
- "Sex" is a BREEDING ROLE, not inherited.
- Offspring do not have sex; we assign roles when using a genotype as a parent:
  - Female role (F): must be allowed_as_female_parent(genotype)
  - Male role (M): always allowed

NEW IMPORTANT CHANGE:
- Stock/genotype validity is validated in BOTH:
  - Manage Stocks tab (when adding new stock)
  - Planner tab (when running planner)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import pandas as pd
from pathlib import Path

from lab_stocks import read_lab_stocks, get_stock_by_name
from genotype_parser import external_to_internal, internal_to_external
from target_planner import plan_to_target, BreedingPlan, allowed_as_female_parent
from cross_logic import validate_stock_genotype


class TargetPlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Drosophila Target Genotype Planner")
        self.root.geometry("1200x800")

        try:
            self.lab_stocks = read_lab_stocks()
        except FileNotFoundError:
            messagebox.showerror("Error", "lab stocks.xlsx not found!")
            self.lab_stocks = []
        except Exception as e:
            messagebox.showerror("Error", f"Error reading lab stocks: {e}")
            self.lab_stocks = []

        self.stock_names = [stock["name"] for stock in self.lab_stocks]
        self.current_plan: Optional[BreedingPlan] = None

        self._create_widgets()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _create_widgets(self):
        style = ttk.Style()
        try:
            style.theme_use("aqua")
        except Exception:
            pass

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.planning_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.planning_frame, text="Planner")
        self._create_planning_tab()

        self.stocks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stocks_frame, text="Manage Stocks")
        self._create_stocks_tab()

        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self._create_results_tab()

    def _create_planning_tab(self):
        left_panel = ttk.Frame(self.planning_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        ttk.Label(left_panel, text="Parent Stocks", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(
            left_panel,
            text="Note: planner may swap breeding roles internally to shorten the scheme.",
        ).pack(anchor=tk.W, pady=(0, 10))

        # Parent 1
        ttk.Label(left_panel, text="Parent 1 (initial):", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(5, 0))
        p1_frame = ttk.Frame(left_panel)
        p1_frame.pack(fill=tk.X, pady=(0, 5))

        self.stock1_var = tk.StringVar()
        self.stock1_combo = ttk.Combobox(p1_frame, textvariable=self.stock1_var, values=self.stock_names, width=30)
        self.stock1_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stock1_combo.bind("<<ComboboxSelected>>", lambda e: self._show_stock_info(1))

        self.stock1_info = ttk.Label(left_panel, text="", wraplength=300)
        self.stock1_info.pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(left_panel, text="Or enter parent 1 genotype directly:").pack(anchor=tk.W)
        self.stock1_manual_var = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.stock1_manual_var, width=35).pack(fill=tk.X, pady=(0, 15))

        # Parent 2
        ttk.Label(left_panel, text="Parent 2 (initial):", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(5, 0))
        p2_frame = ttk.Frame(left_panel)
        p2_frame.pack(fill=tk.X, pady=(0, 5))

        self.stock2_var = tk.StringVar()
        self.stock2_combo = ttk.Combobox(p2_frame, textvariable=self.stock2_var, values=self.stock_names, width=30)
        self.stock2_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stock2_combo.bind("<<ComboboxSelected>>", lambda e: self._show_stock_info(2))

        self.stock2_info = ttk.Label(left_panel, text="", wraplength=300)
        self.stock2_info.pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(left_panel, text="Or enter parent 2 genotype directly:").pack(anchor=tk.W)
        self.stock2_manual_var = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.stock2_manual_var, width=35).pack(fill=tk.X, pady=(0, 15))

        # Target
        ttk.Label(left_panel, text="Target Genotype", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(left_panel, text="Format: 2:a/b 3:a/b 4:a/b").pack(anchor=tk.W, pady=(0, 5))
        self.target_var = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.target_var, width=35).pack(fill=tk.X, pady=(0, 15))

        # Max generations
        ttk.Label(left_panel, text="Max Generations:").pack(anchor=tk.W)
        self.max_gen_var = tk.StringVar(value="2")
        ttk.Spinbox(left_panel, from_=1, to=5, textvariable=self.max_gen_var, width=10).pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X)

        self.run_button = ttk.Button(button_frame, text="Run Planner", command=self._run_planner)
        self.run_button.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self._clear_inputs).pack(side=tk.LEFT)

        # Right preview
        right_panel = ttk.Frame(self.planning_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)

        ttk.Label(right_panel, text="Preview & Results", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.preview_text = tk.Text(right_panel, height=30, width=60, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.preview_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.preview_text.yview)

    def _create_stocks_tab(self):
        # Simple add-stock panel only (keeps your file shorter + stable)
        frame = ttk.LabelFrame(self.stocks_frame, text="Add New Stock", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame, text="Stock Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.new_stock_name = ttk.Entry(frame, width=30)
        self.new_stock_name.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0), pady=5)

        ttk.Label(frame, text="Stock Owner:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.new_stock_owner = ttk.Entry(frame, width=30)
        self.new_stock_owner.grid(row=1, column=1, sticky=tk.EW, padx=(5, 0), pady=5)

        ttk.Label(frame, text="Genotype:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.new_stock_genotype = ttk.Entry(frame, width=50)
        self.new_stock_genotype.grid(row=2, column=1, sticky=tk.EW, padx=(5, 0), pady=5)

        ttk.Label(frame, text="Notes (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.new_stock_notes = ttk.Entry(frame, width=50)
        self.new_stock_notes.grid(row=3, column=1, sticky=tk.EW, padx=(5, 0), pady=5)

        ttk.Button(frame, text="Add Stock", command=self._add_new_stock).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        frame.columnconfigure(1, weight=1)

        # show current stocks
        list_frame = ttk.LabelFrame(self.stocks_frame, text="Current Stocks", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("Name", "Owner", "Genotype", "Notes")
        self.stocks_tree = ttk.Treeview(list_frame, columns=columns, height=15)
        self.stocks_tree.column("#0", width=0, stretch=tk.NO)
        for col, w in zip(columns, [120, 120, 420, 250]):
            self.stocks_tree.column(col, width=w, anchor=tk.W)
            self.stocks_tree.heading(col, text=col)

        self.stocks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.stocks_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stocks_tree.configure(yscrollcommand=scrollbar.set)

        self._refresh_stocks_list()

    def _create_results_tab(self):
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(self.results_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)

    # ---------------------------------------------------------------------
    # Stock info helpers
    # ---------------------------------------------------------------------

    def _role_eligibility_text(self, internal_genotype) -> str:
        female_ok = allowed_as_female_parent(internal_genotype)
        return f"Female-role eligible: {'YES' if female_ok else 'NO'}\nMale-role eligible: YES"

    def _show_stock_info(self, which: int):
        try:
            if which == 1:
                stock_name = self.stock1_var.get()
                label = self.stock1_info
            else:
                stock_name = self.stock2_var.get()
                label = self.stock2_info

            if not stock_name:
                return

            stock = get_stock_by_name(self.lab_stocks, stock_name)
            internal_g = stock["internal_genotype"]
            info_text = f"Genotype: {stock['genotype']}\n{self._role_eligibility_text(internal_g)}"
            label.config(text=info_text, foreground="black")
        except Exception:
            label.config(text="", foreground="black")

    # ---------------------------------------------------------------------
    # Run planner (NOW validates stocks here too)
    # ---------------------------------------------------------------------

    def _run_planner(self):
        stock1_name = self.stock1_var.get().strip()
        stock1_manual = self.stock1_manual_var.get().strip()
        stock2_name = self.stock2_var.get().strip()
        stock2_manual = self.stock2_manual_var.get().strip()
        target = self.target_var.get().strip()
        max_gen_str = self.max_gen_var.get().strip()

        if not stock1_name and not stock1_manual:
            messagebox.showwarning("Input Error", "Please select or enter Parent 1 stock genotype")
            return

        if not stock2_name and not stock2_manual:
            messagebox.showwarning("Input Error", "Please select or enter Parent 2 stock genotype")
            return

        if not target:
            messagebox.showwarning("Input Error", "Please enter a target genotype")
            return

        try:
            max_gen = int(max_gen_str)
            if max_gen < 1 or max_gen > 5:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Max generations must be a number between 1 and 5")
            return

        # Parse + validate parents + target BEFORE planning
        try:
            if stock1_manual:
                g1, _ = external_to_internal(stock1_manual)
                stock1 = {"name": "Custom Stock 1", "genotype": stock1_manual, "internal_genotype": g1, "owner": "manual"}
            else:
                stock1 = get_stock_by_name(self.lab_stocks, stock1_name)

            if stock2_manual:
                g2, _ = external_to_internal(stock2_manual)
                stock2 = {"name": "Custom Stock 2", "genotype": stock2_manual, "internal_genotype": g2, "owner": "manual"}
            else:
                stock2 = get_stock_by_name(self.lab_stocks, stock2_name)

            # Validate stock genotypes in PLANNER TAB
            validate_stock_genotype(stock1["internal_genotype"], context="Parent 1")
            validate_stock_genotype(stock2["internal_genotype"], context="Parent 2")

            target_internal, _ = external_to_internal(target)
            validate_stock_genotype(target_internal, context="Target genotype")

        except ValueError as e:
            messagebox.showwarning("Invalid stock/genotype", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse inputs:\n{e}")
            return

        selected_stocks = [stock1, stock2]

        try:
            self.run_button.config(state=tk.DISABLED)
            self.root.update()

            self.current_plan = plan_to_target(selected_stocks, target, max_gen)

            if self.current_plan:
                self._display_results()
                messagebox.showinfo("Success", "Plan found! Check the Results tab.")
            else:
                messagebox.showinfo("No Plan", "No breeding plan found within the specified generations.")
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, "No breeding plan found within the specified generations.")

        except Exception as e:
            messagebox.showerror("Error", f"Error running planner:\n{e}")
        finally:
            self.run_button.config(state=tk.NORMAL)

    # ---------------------------------------------------------------------
    # Results display
    # ---------------------------------------------------------------------

    def _display_results(self):
        if not self.current_plan:
            return
        text = self._format_plan(self.current_plan)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, text)

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)

    def _format_plan(self, plan: BreedingPlan) -> str:
        lines = [
            "=" * 100,
            "BREEDING PLAN TO REACH TARGET GENOTYPE",
            "=" * 100,
            f"\nTotal Generations: {plan.total_generations}",
            f"Overall Success Probability: {plan.target_probability:.2%}\n",
            "-" * 100,
        ]

        for i, step in enumerate(plan.steps, 1):
            lines.append(f"\n\nCROSS {i}")
            lines.append("=" * 100)

            p1_gen = internal_to_external(step.parent1_genotype, "F")
            p2_gen = internal_to_external(step.parent2_genotype, "F")

            lines.append(f"\nParent 1: {step.parent1_name}")
            lines.append("  Role: F (female)")
            lines.append(f"  Genotype: {p1_gen}")
            lines.append(f"  Female-role eligible: {'YES ✓' if allowed_as_female_parent(step.parent1_genotype) else 'NO ✗'}")

            lines.append(f"\nParent 2: {step.parent2_name}")
            lines.append("  Role: M (male)")
            lines.append(f"  Genotype: {p2_gen}")
            lines.append("  Male-role eligible: YES ✓")

            lines.append("\nCROSS SCHEME:")
            lines.append(f"  {step.parent1_name} (F-role) × {step.parent2_name} (M-role)")

            if step.intermediate_genotype:
                inter = internal_to_external(step.intermediate_genotype, "F")
                lines.append(f"\nOFFSPRING (F{step.generation}): multiple genotypes")
                lines.append("\n▶▶▶ SELECT AS VIRTUAL STOCK FOR NEXT CROSS ◀◀◀")
                lines.append(f"  Genotype: {inter}")
                lines.append(f"  Frequency: ~{step.target_probability:.2%}")
                lines.append(
                    f"  Female-role eligible later: {'YES' if allowed_as_female_parent(step.intermediate_genotype) else 'NO (male-role only)'}"
                )
            else:
                tgt = internal_to_external(plan.target_genotype, "F")
                lines.append("\nOFFSPRING (TARGET):")
                lines.append(f"  Genotype: {tgt}")
                lines.append(f"  Success Frequency in this cross: ~{step.target_probability:.2%}")

        lines.append("\n" + "=" * 100)
        return "\n".join(lines)

    # ---------------------------------------------------------------------
    # Stocks
    # ---------------------------------------------------------------------

    def _refresh_stocks_list(self):
        for item in self.stocks_tree.get_children():
            self.stocks_tree.delete(item)

        for s in self.lab_stocks:
            self.stocks_tree.insert(
                "", tk.END,
                values=(s["name"], s.get("owner", ""), s["genotype"], s.get("notes", ""))
            )

    def _add_new_stock(self):
        name = self.new_stock_name.get().strip()
        owner = self.new_stock_owner.get().strip()
        genotype = self.new_stock_genotype.get().strip()
        notes = self.new_stock_notes.get().strip()

        if not name or not genotype:
            messagebox.showwarning("Input Error", "Please fill in Name and Genotype")
            return

        # Parse + validate on ADD STOCK (stock management tab)
        try:
            internal_g, _ = external_to_internal(genotype)
            validate_stock_genotype(internal_g, context=f"new stock '{name}'")
        except ValueError as e:
            messagebox.showwarning("Invalid Stock Genotype", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Invalid genotype format:\n{e}")
            return

        try:
            excel_path = Path("lab stocks.xlsx")
            if excel_path.exists():
                df = pd.read_excel(excel_path)
            else:
                df = pd.DataFrame(columns=["stock owner", "stock number", "chromosome 2", "chromosome 3", "chromosome 4", "notes"])

            chrom_data = {}
            for chrom in ["2", "3", "4"]:
                if chrom in internal_g:
                    a1, a2 = internal_g[chrom]
                    chrom_data[chrom] = f"{a1}/{a2}"
                else:
                    chrom_data[chrom] = "+/+"

            new_row = pd.DataFrame([{
                "stock owner": owner or "lab",
                "stock number": name,
                "chromosome 2": chrom_data.get("2", "+/+"),
                "chromosome 3": chrom_data.get("3", "+/+"),
                "chromosome 4": chrom_data.get("4", "+/+"),
                "notes": notes,
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(excel_path, index=False)

            self.lab_stocks = read_lab_stocks()
            self.stock_names = [stock["name"] for stock in self.lab_stocks]
            self.stock1_combo["values"] = self.stock_names
            self.stock2_combo["values"] = self.stock_names
            self._refresh_stocks_list()

            self.new_stock_name.delete(0, tk.END)
            self.new_stock_owner.delete(0, tk.END)
            self.new_stock_genotype.delete(0, tk.END)
            self.new_stock_notes.delete(0, tk.END)

            messagebox.showinfo("Success", f"Stock '{name}' added successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Error adding stock:\n{e}")

    def _clear_inputs(self):
        self.stock1_var.set("")
        self.stock1_manual_var.set("")
        self.stock2_var.set("")
        self.stock2_manual_var.set("")
        self.target_var.set("")
        self.stock1_info.config(text="")
        self.stock2_info.config(text="")
        self.preview_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    TargetPlannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
