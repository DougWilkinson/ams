# menu.py

import asyncio
from logger import info, error, debug
import time

# Simple 2 button menu logic to create a menu and navigate
# press up to cycle through options
# down to select option (OK)
# up again to cycle through values
# down again to select value (OK)

# d_options = [ [ "profiles", "12/24", "style", "exit" ], 
# 			 [ "option1-value1", "option1-value2", "option1-value3", "" ], 
# 			 [ "option2-value1", "option2-value2", "option2-value3", "" ],	
# 			 [ "option3-value1", "option3-value2", "option3-value3", "" ] ]

class Menu:
	# def __init__(self, menu, next_event, select_event, menu_active_event, item_selected_event, menu_changed_event):
	def __init__(self, menu):
		self.menu = menu
		self.row = 0
		self.item = 0
		self.active = False
		self.last_event_seconds = time.time()

		# asyncio.create_task(self.next_button_handler(next_event, menu_active_event) )
		# asyncio.create_task(self.select_button_handler(select_event, menu_active_event, item_selected_event) )

	def next_button_handler(self):
		
		self.last_event_seconds = time.time()
		if not self.active:
			self.active = True
			return
		
		self.item += 1
		if self.item == len(self.menu[self.row]):
			self.item = 0

	def select_button_handler(self) -> tuple:

		self.last_event_seconds = time.time()
		if not self.active:
			self.active = True
			return None
		
		# if on row 0 and exit selected, exit menu
		if self.row == 0 and self.item == len(self.menu[self.row]) - 1:
			debug("menu exit sequence")
			self.active = False
			return None
		
		# if on row 0 and not exit selected, go to row 1 + option value
		# to select values for that option
		if self.row == 0 and self.item < len(self.menu[self.row]) - 1:
			self.row = self.item + 1
			self.last_row_item = self.item
			self.item = 0
			debug("menu option selected: row={}, item={}, last_row_item={}".format(self.row, self.item, self.last_row_item) )
			return None
		
		# if select on last item in row, go back to options (row 0)
		if self.item == len(self.menu[self.row]) - 1:
			debug("value menu exited back to option list")
			self.row = 0
			self.item = self.last_row_item
			return ""
				
		# value was selected, disable menu and return option index (-1) and value index
		self.active = False
		error("menu value selected: {}, {}".format(self.row, self.item))
		return (self.row - 1, self.item)
	
	# async def next_button_handler(self, next_event, menu_active_event):
	# 	while True:
	# 		await menu_active_event.wait()
	# 		await next_event.wait()
			
	# 		# reset if menu exited while waiting for next event
	# 		if not menu_active_event.is_set():
	# 			continue

	# 		self.item += 1
	# 		if self.item == len(self.menu[self.row]):
	# 			self.item = 0
	# 		next_event.clear()

	# async def select_button_handler(self, select_event, menu_active_event, item_selected_event):
	# 	while True:
	# 		await menu_active_event.wait()
	# 		await select_event.wait()

	# 		# if on row 0 and exit selected, clear menu_active_event
	# 		if self.row == 0 and self.item == len(self.menu[self.row]) - 1:
	# 			select_event.clear()
	# 			menu_active_event.clear()
	# 			continue
			
	# 		# if on row 0 and not exit selected, go to row 1 + item value
	# 		# to select values for that option
	# 		if self.row == 0 and self.item < len(self.menu[self.row]) - 1:
	# 			self.row = self.item + 1
	# 			self.item = 0
	# 			select_event.clear()
	# 			continue

	# 		# if select on last item in row, go back to options (row 0)
	# 		if self.item == len(self.menu[self.row]) - 1:
	# 			self.item = 0
	# 			self.row = 0
	# 			select_event.clear()
	# 			continue
			
	# 		# value was selected, set selected flag
	# 		item_selected_event.set()
	# 		select_event.clear()
	# 		menu_active_event.clear()

	def selected_item(self) -> tuple:
		return (self.menu[0, self.item], self.menu[self.row][self.item] )
	
	def reset_menu(self):
		self.row = 0
		self.item = 0
