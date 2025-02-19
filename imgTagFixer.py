import wx
import os
from lxml import etree
import re

class XMLProcessor(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='XML Image Placement Processor', size=(500, 400))
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        select_btn = wx.Button(panel, label='Select Folder')
        select_btn.Bind(wx.EVT_BUTTON, self.on_select_folder)
        vbox.Add(select_btn, 0, wx.ALL | wx.CENTER, 5)
        
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.log, 1, wx.ALL | wx.EXPAND, 5)
        
        panel.SetSizer(vbox)
        self.Center()

    def get_xml_header(self, content):
        # XML 선언부와 DOCTYPE을 포함한 전체 헤더를 추출
        header_pattern = r'(<\?xml[^>]+\?>[\s]*<!DOCTYPE[^>]+\]>)'
        match = re.match(header_pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        return ''

    def process_xml(self, xml_path):
        try:
            # 원본 파일 내용 읽기
            with open(xml_path, 'r', encoding='utf-8') as file:
                original_content = file.read()

            # XML 파서 설정
            parser = etree.XMLParser(dtd_validation=False, load_dtd=True, resolve_entities=False)
            tree = etree.parse(xml_path, parser)
            root = tree.getroot()
            modified = False

            # 모든 image 태그 처리
            for image in root.findall(".//image"):
                placement = image.get('placement')
                if placement is None:
                    continue

                parents = [parent.tag for parent in image.iterancestors()]
                in_table = 'table' in parents

                if in_table:
                    if 'fig' in parents:
                        if placement != 'break':
                            image.set('placement', 'break')
                            modified = True
                    else:
                        if placement != 'inline':
                            image.set('placement', 'inline')
                            modified = True
                else:
                    if 'p' in parents:
                        if placement != 'inline':
                            image.set('placement', 'inline')
                            modified = True
                    else:
                        if placement != 'break':
                            image.set('placement', 'break')
                            modified = True

            if modified:
                # 원본 헤더 추출
                original_header = original_content.split('<topic')[0].strip()
                
                # 수정된 XML 내용을 문자열로 변환
                modified_content = etree.tostring(root, encoding='unicode', pretty_print=True)
                
                # 수정된 내용 저장
                with open(xml_path, 'w', encoding='utf-8') as file:
                    file.write(original_header + '\n')
                    file.write(modified_content)
                return True
            return False

        except Exception as e:
            raise Exception(f"Error processing {os.path.basename(xml_path)}: {str(e)}")

    def on_select_folder(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
            self.log.Clear()
            self.process_folder(folder_path)
        dlg.Destroy()

    def process_folder(self, folder_path):
        total_files = 0
        modified_files = 0
        error_files = 0

        self.log.AppendText(f"Processing folder: {folder_path}\n")
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.xml'):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    try:
                        was_modified = self.process_xml(file_path)
                        if was_modified:
                            modified_files += 1
                            self.log.AppendText(f"Modified: {file}\n")
                        else:
                            self.log.AppendText(f"No changes needed: {file}\n")
                    except Exception as e:
                        error_files += 1
                        self.log.AppendText(f"Error: {str(e)}\n")

        self.log.AppendText(f"\nProcess completed:\n")
        self.log.AppendText(f"Total XML files: {total_files}\n")
        self.log.AppendText(f"Modified files: {modified_files}\n")
        self.log.AppendText(f"Errors: {error_files}\n")

def main():
    app = wx.App()
    frame = XMLProcessor()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
