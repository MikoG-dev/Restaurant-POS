"""
Printer utilities for kitchen receipt printing
Supports ESC/POS commands and plain text formatting for thermal printers
"""

import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class PrinterFormatter:
    """Handles formatting for thermal receipt printers"""
    
    # ESC/POS Commands
    ESC = '\x1b'
    INIT = ESC + '@'  # Initialize printer
    BOLD_ON = ESC + 'E' + '\x01'  # Bold text on
    BOLD_OFF = ESC + 'E' + '\x00'  # Bold text off
    UNDERLINE_ON = ESC + '-' + '\x01'  # Underline on
    UNDERLINE_OFF = ESC + '-' + '\x00'  # Underline off
    CENTER = ESC + 'a' + '\x01'  # Center alignment
    LEFT = ESC + 'a' + '\x00'  # Left alignment
    RIGHT = ESC + 'a' + '\x02'  # Right alignment
    CUT_PAPER = ESC + 'm'  # Cut paper
    FEED_LINE = '\n'
    DOUBLE_HEIGHT = ESC + '!' + '\x10'  # Double height text
    NORMAL_TEXT = ESC + '!' + '\x00'  # Normal text
    
    def __init__(self, paper_width: int = 32, use_escpos: bool = True):
        """
        Initialize printer formatter
        
        Args:
            paper_width: Width of receipt paper in characters (default 32 for 58mm)
            use_escpos: Whether to use ESC/POS commands (True) or plain text (False)
        """
        self.paper_width = paper_width
        self.use_escpos = use_escpos
        
    def center_text(self, text: str) -> str:
        """Center text within paper width"""
        if len(text) >= self.paper_width:
            return text
        padding = (self.paper_width - len(text)) // 2
        return ' ' * padding + text
    
    def left_right_text(self, left: str, right: str) -> str:
        """Align text with left and right justification"""
        total_len = len(left) + len(right)
        if total_len >= self.paper_width:
            return left + ' ' + right
        spaces = self.paper_width - total_len
        return left + ' ' * spaces + right
    
    def create_line(self, char: str = '-') -> str:
        """Create a line separator"""
        return char * self.paper_width
    
    def wrap_text(self, text: str, width: Optional[int] = None) -> List[str]:
        """Wrap text to fit within specified width"""
        if width is None:
            width = self.paper_width
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word + " ") <= width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.rstrip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.rstrip())
        
        return lines
    
    def format_header(self, title: str) -> str:
        """Format receipt header"""
        lines = []
        if self.use_escpos:
            lines.append(self.INIT)  # Initialize printer
            lines.append(self.CENTER + self.BOLD_ON + self.DOUBLE_HEIGHT)
        
        lines.append(self.center_text(title))
        
        if self.use_escpos:
            lines.append(self.NORMAL_TEXT + self.BOLD_OFF + self.LEFT)
        
        lines.append(self.create_line('='))
        return '\n'.join(lines)
    
    def format_section_header(self, title: str) -> str:
        """Format section header"""
        lines = []
        if self.use_escpos:
            lines.append(self.BOLD_ON)
        
        lines.append(title)
        
        if self.use_escpos:
            lines.append(self.BOLD_OFF)
        
        lines.append(self.create_line('-'))
        return '\n'.join(lines)
    
    def format_item_line(self, quantity: int, name: str, notes: str = "") -> str:
        """Format an item line with quantity and name"""
        lines = []
        
        # Main item line
        qty_text = f"{quantity}x"
        if len(qty_text + name) <= self.paper_width:
            lines.append(f"{qty_text} {name}")
        else:
            lines.append(qty_text)
            # Wrap long item names
            wrapped_names = self.wrap_text(name, self.paper_width - 2)
            for wrapped_name in wrapped_names:
                lines.append(f"  {wrapped_name}")
        
        # Add notes if any
        if notes:
            note_lines = self.wrap_text(f"Note: {notes}", self.paper_width - 2)
            for note_line in note_lines:
                lines.append(f"  {note_line}")
        
        return '\n'.join(lines)
    
    def format_footer(self, restaurant_name: str, timestamp: str) -> str:
        """Format receipt footer"""
        lines = []
        lines.append(self.create_line('='))
        lines.append(self.center_text(restaurant_name))
        lines.append(self.center_text(timestamp))
        
        if self.use_escpos:
            lines.append(self.FEED_LINE * 3)  # Extra feed before cut
            lines.append(self.CUT_PAPER)  # Cut paper
        else:
            lines.append('\n' * 3)  # Extra spacing for manual cutting
        
        return '\n'.join(lines)


class KitchenPrinter:
    """Handles kitchen receipt printing operations"""
    
    def __init__(self, printer_name: Optional[str] = None, paper_width: int = 32, use_escpos: bool = True):
        """
        Initialize kitchen printer
        
        Args:
            printer_name: Name of the printer (None for default)
            paper_width: Width of receipt paper in characters
            use_escpos: Whether to use ESC/POS commands
        """
        self.printer_name = printer_name
        self.formatter = PrinterFormatter(paper_width, use_escpos)
        self.use_escpos = use_escpos
    
    def get_available_printers(self) -> List[str]:
        """Get list of available printers on Windows"""
        try:
            # Use PowerShell to get printer list
            result = subprocess.run([
                'powershell', '-Command', 
                'Get-Printer | Select-Object Name | ForEach-Object { $_.Name }'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                printers = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return printers
            else:
                return []
        except Exception:
            return []
    
    def print_to_file(self, content: str, filename: str = None) -> bool:
        """Print content to a file (for testing or when no printer available)"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"kitchen_ticket_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Kitchen ticket saved to: {filename}")
            return True
        except Exception as e:
            print(f"Error saving kitchen ticket to file: {e}")
            return False
    
    def print_to_printer(self, content: str) -> bool:
        """Send content directly to printer"""
        try:
            if sys.platform == "win32":
                return self._print_windows(content)
            else:
                return self._print_unix(content)
        except Exception as e:
            print(f"Error printing to printer: {e}")
            return False
    
    def _print_windows(self, content: str) -> bool:
        """Print on Windows using direct printer access"""
        try:
            import tempfile
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_filename = temp_file.name
            
            # Print using Windows print command
            if self.printer_name:
                cmd = f'print /D:"{self.printer_name}" "{temp_filename}"'
            else:
                cmd = f'print "{temp_filename}"'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Clean up temp file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            if result.returncode == 0:
                print("Kitchen ticket sent to printer successfully")
                return True
            else:
                print(f"Print command failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Windows printing error: {e}")
            return False
    
    def _print_unix(self, content: str) -> bool:
        """Print on Unix/Linux systems using lp command"""
        try:
            if self.printer_name:
                cmd = ['lp', '-d', self.printer_name]
            else:
                cmd = ['lp']
            
            result = subprocess.run(cmd, input=content, text=True, capture_output=True)
            
            if result.returncode == 0:
                print("Kitchen ticket sent to printer successfully")
                return True
            else:
                print(f"Print command failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Unix printing error: {e}")
            return False
    
    def format_kitchen_ticket(self, order_data: Dict, items: List[Dict], settings: Dict) -> str:
        """Format a complete kitchen ticket"""
        lines = []
        
        # Header
        lines.append(self.formatter.format_header("KITCHEN ORDER"))
        lines.append("")
        
        # Order information
        lines.append(self.formatter.format_section_header("ORDER DETAILS"))
        lines.append(f"Order #: {order_data.get('id', 'N/A')}")
        lines.append(f"Table: {order_data.get('table_number', 'N/A')}")
        lines.append(f"Waiter: {order_data.get('waiter_name', 'Unassigned')}")
        lines.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        lines.append(f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        lines.append("")
        
        # Items section
        lines.append(self.formatter.format_section_header("ITEMS TO PREPARE"))
        
        for item in items:
            item_line = self.formatter.format_item_line(
                quantity=item.get('quantity', 1),
                name=item.get('item_name', 'Unknown Item'),
                notes=item.get('notes', '')
            )
            lines.append(item_line)
            lines.append("")  # Space between items
        
        # Summary
        lines.append(self.formatter.format_section_header("ORDER SUMMARY"))
        total_items = sum(item.get('quantity', 1) for item in items)
        lines.append(f"Total Items: {total_items}")
        
        if order_data.get('total_amount'):
            lines.append(f"Order Total: {order_data['total_amount']:.2f} Br")
        
        lines.append("")
        
        # Footer
        restaurant_name = settings.get('restaurant_name', 'Restaurant POS')
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        lines.append(self.formatter.format_footer(restaurant_name, f"Printed: {timestamp}"))
        
        return '\n'.join(lines)
    
    def print_kitchen_ticket(self, order_data: Dict, items: List[Dict], settings: Dict, 
                           save_to_file: bool = True, send_to_printer: bool = True) -> bool:
        """
        Print kitchen ticket with multiple output options
        
        Args:
            order_data: Order information dictionary
            items: List of order items
            settings: Restaurant settings
            save_to_file: Whether to save ticket to file
            send_to_printer: Whether to send to printer
        
        Returns:
            bool: True if at least one output method succeeded
        """
        try:
            # Format the ticket
            ticket_content = self.format_kitchen_ticket(order_data, items, settings)
            
            success = False
            
            # Save to file if requested
            if save_to_file:
                if self.print_to_file(ticket_content):
                    success = True
            
            # Send to printer if requested
            if send_to_printer:
                if self.print_to_printer(ticket_content):
                    success = True
                else:
                    # Fallback to file if printer fails
                    print("Printer failed, saving to file as backup...")
                    if self.print_to_file(ticket_content, f"kitchen_ticket_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"):
                        success = True
            
            # Always show in console for debugging
            print("\n" + "="*50)
            print("KITCHEN TICKET GENERATED")
            print("="*50)
            print(ticket_content)
            print("="*50 + "\n")
            
            return success
            
        except Exception as e:
            print(f"Error in print_kitchen_ticket: {e}")
            return False