import js
from pyscript import document
from pyodide.ffi import create_proxy
from abc import ABC, abstractmethod
from datetime import datetime

class AbstractWidget(ABC):
  def __init__(self, element_id):
    self.element_id = element_id
    self._element = None
    
  @property
  def element(self):
    if not self._element:
      self._element = document.querySelector(f"#{self.element_id}")
    return self._element
  
  @abstractmethod
  def drawWidget(self):
    pass

class Navbar(AbstractWidget):
  def __init__(self, element_id):
    AbstractWidget.__init__(self, element_id)
    
  def drawWidget(self):
    self.navbar = document.createElement("div")
    self.navbar.className = "backdrop-blur-lg w-screen h-24 text-white flex justify-center items-center fixed z-10"
    self.title = document.createElement("a")
    self.title.innerHTML = "SukSaang"
    self.title.className = "font-signature font-extrabold text-5xl"
    self.navbar.appendChild(self.title)
    self.element.appendChild(self.navbar)
    
class MainContent(AbstractWidget):
  def __init__(self, element_id):
    AbstractWidget.__init__(self, element_id)
    
  def drawWidget(self, widgets):
    self.content = document.createElement("div")
    self.content.id = "content"
    self.content.className = "pt-28 flex flex-col gap-2 items-center h-screen w-screen bg-gradient-to-br from from-zinc-950 via-gray-800 to-gray-700"
    self.element.appendChild(self.content)
    
    for widget in widgets:
      widget.drawWidget()

class Home(AbstractWidget):
  def __init__(self, element_id):
    AbstractWidget.__init__(self, element_id)
    
  def drawWidget(self):
    self.customer = document.createElement("div")
    self.customer.className = "uppercase p-10 bg-gray-700 w-fit text-white"
    self.customer.innerHTML = "customer"
    self.element.appendChild(self.customer)
    
    self.admin = document.createElement("div")
    self.admin.className = "uppercase p-10 bg-gray-700 w-fit text-white" 
    self.admin.innerHTML = "admin"
    self.element.appendChild(self.admin)
    
if __name__ == "__main__":
  Navbar("app").drawWidget()
  
  content = MainContent("app")
  content.drawWidget([Home("content")])