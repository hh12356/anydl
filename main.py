import flet as ft
from ui.app import main_app
import uvicorn

# Fix for uvicorn 0.23.2 compatibility with flet
old_init = uvicorn.Config.__init__
def new_init(self, *args, **kwargs):
    if kwargs.get('ws') == 'websockets-sansio':
        kwargs['ws'] = 'auto'
    old_init(self, *args, **kwargs)
uvicorn.Config.__init__ = new_init

if __name__ == '__main__':
    ft.run(main_app, view=ft.AppView.FLET_APP)
