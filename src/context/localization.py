from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


DEFAULT_LOCALE = "pt-BR"
FALLBACK_LOCALE = "en"
SUPPORTED_LOCALES = ("pt-BR", "en")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.name": "ContExt",
        "window.title": "ContExt | PyQt6 Graph",
        "menu.file": "File",
        "menu.edit": "Edit",
        "menu.view": "View",
        "menu.language": "Language",
        "toolbar.main": "Main",
        "action.open_pipeline": "Open Pipeline...",
        "action.save_pipeline": "Save Pipeline...",
        "action.save_preview": "Save Preview as PNG...",
        "action.open_image": "Open Image...",
        "action.delete_selected": "Delete Selected",
        "action.quit": "Quit",
        "dock.properties": "Properties",
        "dock.preview": "Preview",
        "dialog.open_pipeline.title": "Open Pipeline",
        "dialog.open_pipeline.filter": "Context Pipeline (*.ctxp *.json)",
        "dialog.save_pipeline.title": "Save Pipeline",
        "dialog.save_pipeline.filter": "Context Pipeline (*.ctxp);;JSON (*.json)",
        "dialog.save_preview.title": "Save Preview as PNG",
        "dialog.save_preview.filter": "PNG Image (*.png)",
        "dialog.open_image.title": "Open Image",
        "dialog.open_image.filter": "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        "status.loaded_image": "Loaded {name}",
        "status.loaded_pipeline": "Loaded pipeline {name}",
        "status.saved_pipeline": "Saved pipeline {name}",
        "status.saved_preview": "Saved preview {name}",
        "status.processing": "Processing graph...",
        "status.ready": "Ready",
        "status.theme_enabled": "{theme} enabled",
        "status.language_enabled": "Language set to {language}",
        "theme.name.material_light": "Material Light",
        "theme.name.material_dark": "Material Dark",
        "language.name.pt-BR": "Portuguese (Brazil)",
        "language.name.en": "English",
        "graph.menu.add_source": "Add Source",
        "graph.menu.add_blur": "Add Blur",
        "graph.menu.add_preview": "Add Preview",
        "graph.menu.delete_selected": "Delete Selected",
        "graph.error.only_one_source": "Only one Source node is allowed.",
        "graph.error.only_one_preview": "Only one Preview node is allowed.",
        "graph.error.unsupported_node_type": "Unsupported node type: {type_name}.",
        "graph.error.connection_self": "A node cannot connect to itself.",
        "graph.error.connection_cycle": "This connection would create a cycle.",
        "graph.error.connection_input_occupied": "That input already has a connection.",
        "graph.error.connection_unknown_node": "The selected node is no longer available.",
        "graph.error.connection_invalid_port": "The selected ports are not compatible.",
        "graph.error.connection_rejected": "This connection is not valid.",
        "graph.error.pipeline_load_failed": "Failed to open pipeline. {message}",
        "graph.error.pipeline_save_failed": "Failed to save pipeline. {message}",
        "panel.none.title": "No node selected",
        "panel.none.description": "Select a node to edit its properties.",
        "panel.source.description": "Loads the working image into the pipeline.",
        "panel.source.path": "Path",
        "panel.source.resolution": "Resolution",
        "panel.source.no_image": "No image loaded",
        "panel.blur.description": "Applies a Gaussian blur to the incoming image. You can also scrub it inside the node.",
        "panel.blur.kernel_size": "Kernel size",
        "panel.preview.description": "Displays the last image flowing through the graph.",
        "panel.preview.status": "Status",
        "panel.preview.waiting": "Waiting for input",
        "panel.preview.ready": "Ready",
        "preview.unavailable": "Preview unavailable",
        "preview.export.unavailable": "There is no preview image to save yet.",
        "node.source.title": "Source",
        "node.source.body.empty": "Load an image",
        "node.source.body.ready": "Image ready",
        "node.blur.title": "Blur",
        "node.blur.body": "Gaussian blur",
        "node.blur.kernel": "Kernel",
        "node.preview.title": "Preview",
        "node.preview.body": "Canvas output",
        "node.status.ready": "READY",
        "node.status.wait": "WAIT",
        "startup.title": "Preparing your workspace",
        "startup.subtitle": "Choose theme and language while the application finishes loading.",
        "startup.select_theme": "Theme",
        "startup.select_language": "Preferred language",
        "startup.continue": "Continue",
        "startup.wait": "Loading components...",
        "startup.auto_continue": "Ready. Opening automatically...",
        "startup.click_continue": "Ready. Click continue to enter the app.",
        "startup.step.preferences": "Loading preferences",
        "startup.step.theme": "Applying theme",
        "startup.step.locale": "Applying language",
        "startup.step.workspace": "Building workspace",
        "startup.ready": "Everything is ready",
    },
    "pt-BR": {
        "app.name": "ContExt",
        "window.title": "ContExt | Grafo PyQt6",
        "menu.file": "Arquivo",
        "menu.edit": "Editar",
        "menu.view": "Visual",
        "menu.language": "Idioma",
        "toolbar.main": "Principal",
        "action.open_pipeline": "Abrir pipeline...",
        "action.save_pipeline": "Salvar pipeline...",
        "action.save_preview": "Salvar preview como PNG...",
        "action.open_image": "Abrir imagem...",
        "action.delete_selected": "Excluir seleção",
        "action.quit": "Sair",
        "dock.properties": "Propriedades",
        "dock.preview": "Pré-visualização",
        "dialog.open_pipeline.title": "Abrir pipeline",
        "dialog.open_pipeline.filter": "Pipeline Context (*.ctxp *.json)",
        "dialog.save_pipeline.title": "Salvar pipeline",
        "dialog.save_pipeline.filter": "Pipeline Context (*.ctxp);;JSON (*.json)",
        "dialog.save_preview.title": "Salvar preview como PNG",
        "dialog.save_preview.filter": "Imagem PNG (*.png)",
        "dialog.open_image.title": "Abrir imagem",
        "dialog.open_image.filter": "Imagens (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        "status.loaded_image": "Imagem carregada: {name}",
        "status.loaded_pipeline": "Pipeline carregada: {name}",
        "status.saved_pipeline": "Pipeline salva: {name}",
        "status.saved_preview": "Preview salvo: {name}",
        "status.processing": "Processando grafo...",
        "status.ready": "Pronto",
        "status.theme_enabled": "{theme} ativado",
        "status.language_enabled": "Idioma alterado para {language}",
        "theme.name.material_light": "Material Claro",
        "theme.name.material_dark": "Material Escuro",
        "language.name.pt-BR": "Português (Brasil)",
        "language.name.en": "Inglês",
        "graph.menu.add_source": "Adicionar Source",
        "graph.menu.add_blur": "Adicionar Blur",
        "graph.menu.add_preview": "Adicionar Preview",
        "graph.menu.delete_selected": "Excluir seleção",
        "graph.error.only_one_source": "Somente um node Source é permitido.",
        "graph.error.only_one_preview": "Somente um node Preview é permitido.",
        "graph.error.unsupported_node_type": "Tipo de node não suportado: {type_name}.",
        "graph.error.connection_self": "Um node não pode se conectar a si mesmo.",
        "graph.error.connection_cycle": "Essa conexão criaria um ciclo.",
        "graph.error.connection_input_occupied": "Essa entrada já possui uma conexão.",
        "graph.error.connection_unknown_node": "O node selecionado não está mais disponível.",
        "graph.error.connection_invalid_port": "As portas selecionadas não são compatíveis.",
        "graph.error.connection_rejected": "Essa conexão não é válida.",
        "graph.error.pipeline_load_failed": "Falha ao abrir a pipeline. {message}",
        "graph.error.pipeline_save_failed": "Falha ao salvar a pipeline. {message}",
        "panel.none.title": "Nenhum node selecionado",
        "panel.none.description": "Selecione um node para editar as propriedades.",
        "panel.source.description": "Carrega a imagem de trabalho para dentro do pipeline.",
        "panel.source.path": "Caminho",
        "panel.source.resolution": "Resolução",
        "panel.source.no_image": "Nenhuma imagem carregada",
        "panel.blur.description": "Aplica um desfoque gaussiano na imagem de entrada. Você também pode ajustar isso dentro do node.",
        "panel.blur.kernel_size": "Tamanho do kernel",
        "panel.preview.description": "Exibe a imagem final que chega ao grafo.",
        "panel.preview.status": "Status",
        "panel.preview.waiting": "Aguardando entrada",
        "panel.preview.ready": "Pronto",
        "preview.unavailable": "Pré-visualização indisponível",
        "preview.export.unavailable": "Ainda não existe uma imagem de preview para salvar.",
        "node.source.title": "Source",
        "node.source.body.empty": "Carregue uma imagem",
        "node.source.body.ready": "Imagem pronta",
        "node.blur.title": "Blur",
        "node.blur.body": "Desfoque gaussiano",
        "node.blur.kernel": "Kernel",
        "node.preview.title": "Preview",
        "node.preview.body": "Saída do canvas",
        "node.status.ready": "PRONTO",
        "node.status.wait": "ESPERA",
        "startup.title": "Preparando seu workspace",
        "startup.subtitle": "Escolha tema e idioma enquanto a aplicação termina de carregar.",
        "startup.select_theme": "Tema",
        "startup.select_language": "Idioma preferido",
        "startup.continue": "Entrar",
        "startup.wait": "Carregando componentes...",
        "startup.auto_continue": "Pronto. Abrindo automaticamente...",
        "startup.click_continue": "Pronto. Clique em entrar para abrir o app.",
        "startup.step.preferences": "Carregando preferências",
        "startup.step.theme": "Aplicando tema",
        "startup.step.locale": "Aplicando idioma",
        "startup.step.workspace": "Montando interface",
        "startup.ready": "Tudo pronto",
    },
}


def translate(locale_code: str, key: str, **kwargs) -> str:
    template = (
        TRANSLATIONS.get(locale_code, {}).get(key)
        or TRANSLATIONS[FALLBACK_LOCALE].get(key)
        or key
    )
    return template.format(**kwargs)


class LocalizationController(QObject):
    localeChanged = pyqtSignal(str)

    def __init__(self, initial_locale: str = DEFAULT_LOCALE) -> None:
        super().__init__()
        self._locale = DEFAULT_LOCALE
        self.set_locale(initial_locale)

    @property
    def locale(self) -> str:
        return self._locale

    def available_locales(self) -> tuple[str, ...]:
        return SUPPORTED_LOCALES

    def set_locale(self, locale_code: str) -> None:
        if locale_code not in SUPPORTED_LOCALES:
            locale_code = FALLBACK_LOCALE
        if locale_code == self._locale:
            return
        self._locale = locale_code
        self.localeChanged.emit(locale_code)

    def tr(self, key: str, **kwargs) -> str:
        return translate(self._locale, key, **kwargs)
