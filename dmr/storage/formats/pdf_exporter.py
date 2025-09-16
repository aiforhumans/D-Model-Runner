"""
PDF exporter for D-Model-Runner conversations.

This module provides PDF export functionality with professional formatting
and custom styling options. Uses reportlab for PDF generation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import io

from ..conversation import Conversation
from ..exporters import BaseExporter

# PDF generation will be implemented using reportlab or weasyprint
# For now, we'll create a base implementation that can be extended


class PDFExporter(BaseExporter):
    """Exporter for PDF format."""
    
    def __init__(self):
        self._pdf_engine = None
        self._check_dependencies()
    
    @property
    def format_name(self) -> str:
        return "PDF"
    
    @property
    def file_extension(self) -> str:
        return "pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    def _check_dependencies(self) -> None:
        """Check for PDF generation dependencies."""
        try:
            import reportlab  # type: ignore[import-untyped]
            self._pdf_engine = 'reportlab'
        except ImportError:
            try:
                import weasyprint  # type: ignore[import-untyped]
                self._pdf_engine = 'weasyprint'
            except ImportError:
                self._pdf_engine = 'html2pdf'  # Fallback using built-in HTML generation
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PDF export options."""
        default_options = {
            'include_metadata': True,
            'include_timestamps': True,
            'page_size': 'A4',
            'margin': '1in',
            'font_family': 'Arial',
            'font_size': 12,
            'add_page_numbers': True,
            'add_header': True,
            'add_footer': True,
            'custom_css': None,
            'title_font_size': 18,
            'header_font_size': 14,
            'timestamp_format': '%Y-%m-%d %H:%M:%S',
            'color_scheme': 'default'
        }
        
        validated = default_options.copy()
        if options:
            validated.update(options)
        
        # Validate page size
        valid_page_sizes = ['A4', 'A3', 'A5', 'Letter', 'Legal']
        if validated['page_size'] not in valid_page_sizes:
            validated['page_size'] = 'A4'
        
        # Validate font size
        if not isinstance(validated['font_size'], (int, float)) or validated['font_size'] < 8:
            validated['font_size'] = 12
        
        return validated
    
    def export(self, conversation: Conversation, output_path: Path, 
               options: Optional[Dict[str, Any]] = None) -> Path:
        """Export conversation to PDF format."""
        validated_options = self.validate_options(options)
        
        if self._pdf_engine == 'reportlab':
            return self._export_with_reportlab(conversation, output_path, validated_options)
        elif self._pdf_engine == 'weasyprint':
            return self._export_with_weasyprint(conversation, output_path, validated_options)
        else:
            return self._export_with_html2pdf(conversation, output_path, validated_options)
    
    def _export_with_reportlab(self, conversation: Conversation, output_path: Path, 
                              options: Dict[str, Any]) -> Path:
        """Export using ReportLab library."""
        try:
            from reportlab.lib.pagesizes import letter, A4, A3, A5, legal  # type: ignore[import-untyped]
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak  # type: ignore[import-untyped]
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import-untyped]
            from reportlab.lib.units import inch  # type: ignore[import-untyped]
            from reportlab.lib import colors  # type: ignore[import-untyped]
            
            # Map page sizes
            page_size_map = {
                'A4': A4, 'A3': A3, 'A5': A5, 'Letter': letter, 'Legal': legal
            }
            page_size = page_size_map.get(options['page_size'], A4)
            
            # Create document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=page_size,
                topMargin=inch,
                bottomMargin=inch,
                leftMargin=inch,
                rightMargin=inch
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=options['title_font_size'],
                fontName='Helvetica-Bold',
                spaceAfter=12
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=options['header_font_size'],
                fontName='Helvetica-Bold',
                spaceAfter=6
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=options['font_size'],
                fontName='Helvetica',
                spaceAfter=6
            )
            
            code_style = ParagraphStyle(
                'CustomCode',
                parent=styles['Code'],
                fontSize=options['font_size'] - 1,
                fontName='Courier',
                leftIndent=20,
                backColor=colors.lightgrey
            )
            
            # Build content
            story = []
            
            # Title
            story.append(Paragraph(conversation.metadata.title, title_style))
            story.append(Spacer(1, 12))
            
            # Metadata
            if options['include_metadata']:
                story.append(Paragraph("Conversation Metadata", header_style))
                
                metadata_text = f"""
                <b>ID:</b> {conversation.id}<br/>
                <b>Model:</b> {conversation.metadata.model}<br/>
                <b>Messages:</b> {len(conversation.messages)}<br/>
                """
                
                if options['include_timestamps']:
                    created = conversation.metadata.created_at.strftime(options['timestamp_format'])
                    updated = conversation.metadata.updated_at.strftime(options['timestamp_format'])
                    metadata_text += f"""
                    <b>Created:</b> {created}<br/>
                    <b>Updated:</b> {updated}<br/>
                    """
                
                if conversation.metadata.tags:
                    tags = ", ".join(conversation.metadata.tags)
                    metadata_text += f"<b>Tags:</b> {tags}<br/>"
                
                if conversation.metadata.description:
                    metadata_text += f"<b>Description:</b> {conversation.metadata.description}<br/>"
                
                story.append(Paragraph(metadata_text, body_style))
                story.append(Spacer(1, 12))
            
            # Messages
            story.append(Paragraph("Conversation Messages", header_style))
            
            for i, message in enumerate(conversation.messages, 1):
                # Message header
                role_header = f"Message {i}: {message.role.title()}"
                story.append(Paragraph(role_header, header_style))
                
                # Timestamp
                if options['include_timestamps']:
                    timestamp = message.timestamp.strftime(options['timestamp_format'])
                    story.append(Paragraph(f"<i>{timestamp}</i>", body_style))
                
                # Content
                content = message.content.replace('\n', '<br/>')
                # Simple code detection
                if any(indicator in content.lower() for indicator in ['def ', 'function', 'class ', 'import ']):
                    story.append(Paragraph(content, code_style))
                else:
                    story.append(Paragraph(content, body_style))
                
                story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            return output_path
            
        except ImportError:
            # Fallback to HTML2PDF if reportlab is not available
            return self._export_with_html2pdf(conversation, output_path, options)
    
    def _export_with_weasyprint(self, conversation: Conversation, output_path: Path, 
                               options: Dict[str, Any]) -> Path:
        """Export using WeasyPrint library."""
        try:
            import weasyprint  # type: ignore[import-untyped]
            
            # Generate HTML content
            html_content = self._generate_html_content(conversation, options)
            
            # Create PDF from HTML
            html_doc = weasyprint.HTML(string=html_content)
            html_doc.write_pdf(str(output_path))
            
            return output_path
            
        except ImportError:
            # Fallback to HTML2PDF
            return self._export_with_html2pdf(conversation, output_path, options)
    
    def _export_with_html2pdf(self, conversation: Conversation, output_path: Path, 
                             options: Dict[str, Any]) -> Path:
        """Export using HTML generation and browser printing (fallback method)."""
        # Generate HTML content
        html_content = self._generate_html_content(conversation, options)
        
        # Save HTML file alongside PDF for manual conversion
        html_path = output_path.with_suffix('.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create a simple text-based PDF alternative
        text_content = self._generate_text_content(conversation, options)
        
        # Write text content as fallback
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PDF Export (Text Format)\n")
            f.write("=" * 50 + "\n\n")
            f.write("Note: Install 'reportlab' or 'weasyprint' for proper PDF generation.\n")
            f.write(f"HTML version saved as: {html_path}\n\n")
            f.write(text_content)
        
        print(f"PDF dependencies not available. Created text file and HTML file at {html_path}")
        print("Install 'reportlab' or 'weasyprint' for proper PDF generation:")
        print("  pip install reportlab")
        print("  pip install weasyprint")
        
        return output_path
    
    def _generate_html_content(self, conversation: Conversation, options: Dict[str, Any]) -> str:
        """Generate HTML content for PDF conversion."""
        css = self._get_default_css(options)
        if options['custom_css']:
            css += "\n" + options['custom_css']
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            f"<title>{conversation.metadata.title}</title>",
            f"<style>{css}</style>",
            "</head>",
            "<body>",
            f"<h1>{conversation.metadata.title}</h1>"
        ]
        
        # Metadata
        if options['include_metadata']:
            html_parts.append("<div class='metadata'>")
            html_parts.append("<h2>Conversation Metadata</h2>")
            html_parts.append("<table>")
            html_parts.append(f"<tr><td><strong>ID:</strong></td><td>{conversation.id}</td></tr>")
            html_parts.append(f"<tr><td><strong>Model:</strong></td><td>{conversation.metadata.model}</td></tr>")
            html_parts.append(f"<tr><td><strong>Messages:</strong></td><td>{len(conversation.messages)}</td></tr>")
            
            if options['include_timestamps']:
                created = conversation.metadata.created_at.strftime(options['timestamp_format'])
                updated = conversation.metadata.updated_at.strftime(options['timestamp_format'])
                html_parts.append(f"<tr><td><strong>Created:</strong></td><td>{created}</td></tr>")
                html_parts.append(f"<tr><td><strong>Updated:</strong></td><td>{updated}</td></tr>")
            
            if conversation.metadata.tags:
                tags = ", ".join(conversation.metadata.tags)
                html_parts.append(f"<tr><td><strong>Tags:</strong></td><td>{tags}</td></tr>")
            
            html_parts.append("</table>")
            html_parts.append("</div>")
        
        # Messages
        html_parts.append("<div class='messages'>")
        html_parts.append("<h2>Conversation Messages</h2>")
        
        for i, message in enumerate(conversation.messages, 1):
            html_parts.append(f"<div class='message message-{message.role}'>")
            html_parts.append(f"<h3>Message {i}: {message.role.title()}</h3>")
            
            if options['include_timestamps']:
                timestamp = message.timestamp.strftime(options['timestamp_format'])
                html_parts.append(f"<p class='timestamp'>{timestamp}</p>")
            
            # Format content
            content = message.content.replace('\n', '<br>')
            if self._is_code_content(content):
                html_parts.append(f"<pre class='code'>{content}</pre>")
            else:
                html_parts.append(f"<div class='content'>{content}</div>")
            
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _generate_text_content(self, conversation: Conversation, options: Dict[str, Any]) -> str:
        """Generate plain text content."""
        lines = []
        
        lines.append(f"Title: {conversation.metadata.title}")
        lines.append("")
        
        if options['include_metadata']:
            lines.append("Metadata:")
            lines.append(f"  ID: {conversation.id}")
            lines.append(f"  Model: {conversation.metadata.model}")
            lines.append(f"  Messages: {len(conversation.messages)}")
            
            if options['include_timestamps']:
                created = conversation.metadata.created_at.strftime(options['timestamp_format'])
                updated = conversation.metadata.updated_at.strftime(options['timestamp_format'])
                lines.append(f"  Created: {created}")
                lines.append(f"  Updated: {updated}")
            
            if conversation.metadata.tags:
                lines.append(f"  Tags: {', '.join(conversation.metadata.tags)}")
            
            lines.append("")
        
        lines.append("Messages:")
        lines.append("-" * 50)
        
        for i, message in enumerate(conversation.messages, 1):
            lines.append(f"\nMessage {i}: {message.role.title()}")
            
            if options['include_timestamps']:
                timestamp = message.timestamp.strftime(options['timestamp_format'])
                lines.append(f"Time: {timestamp}")
            
            lines.append("")
            lines.append(message.content)
            lines.append("-" * 30)
        
        return "\n".join(lines)
    
    def _get_default_css(self, options: Dict[str, Any]) -> str:
        """Get default CSS for HTML to PDF conversion."""
        return f"""
        @page {{
            size: {options['page_size']};
            margin: {options['margin']};
        }}
        
        body {{
            font-family: {options['font_family']}, sans-serif;
            font-size: {options['font_size']}pt;
            line-height: 1.6;
            color: #333;
        }}
        
        h1 {{
            font-size: {options['title_font_size']}pt;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            font-size: {options['header_font_size']}pt;
            color: #34495e;
            margin-top: 30px;
        }}
        
        h3 {{
            font-size: {options['font_size'] + 2}pt;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        
        .metadata table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        .metadata td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        
        .metadata td:first-child {{
            background-color: #f8f9fa;
            font-weight: bold;
            width: 150px;
        }}
        
        .message {{
            margin-bottom: 25px;
            padding: 15px;
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }}
        
        .message-user {{
            border-left-color: #e74c3c;
        }}
        
        .message-assistant {{
            border-left-color: #27ae60;
        }}
        
        .message-system {{
            border-left-color: #f39c12;
        }}
        
        .timestamp {{
            font-style: italic;
            font-size: {options['font_size'] - 2}pt;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        
        .content {{
            margin-top: 10px;
        }}
        
        .code {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: {options['font_size'] - 1}pt;
            overflow-x: auto;
        }}
        """
    
    def _is_code_content(self, content: str) -> bool:
        """Heuristically detect if content is code."""
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'function', 'var ', 'const ', 'let ',
            '#!/', '<?', '<html', '<div', '{', '}', ';'
        ]
        
        content_lower = content.lower()
        for indicator in code_indicators:
            if indicator in content_lower:
                return True
        
        return False
    
    def get_available_engines(self) -> List[str]:
        """Get list of available PDF generation engines."""
        engines = []
        
        try:
            import reportlab  # type: ignore[import-untyped]
            engines.append('reportlab')
        except ImportError:
            pass
        
        try:
            import weasyprint  # type: ignore[import-untyped]
            engines.append('weasyprint')
        except ImportError:
            pass
        
        engines.append('html2pdf')  # Always available as fallback
        
        return engines