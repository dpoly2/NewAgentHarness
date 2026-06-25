"""Models page mixin — delegates to _build_admin_models_tab."""
import tkinter as tk
from pages.constants import *


class ModelsPageMixin:
    def show_models(self):
        self._set_active_nav("Models")
        self._clear_content()
        self._section_header(
            self.content, "🔬 Models Catalog",
            "Browse and toggle available LLM models by provider.",
            actions=[("🔄 Refresh", self.show_models)],
        )
        self._build_admin_models_tab(self.content)
