"""Two practical Arabic handbooks, rendered separately with LibreOffice QA."""
from pathlib import Path
import re,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT=Path('docs');SHOTS=Path('data/validation/studio')
DEVELOPERS='Ahmed G soliman and malak Taha'

def flag(parent,tag,value='1'):
    e=OxmlElement(tag);e.set(qn('w:val'),value);parent.append(e);return e
def direction(p,rtl=True):flag(p._p.get_or_add_pPr(),'w:bidi','1' if rtl else '0')
def text(p,value):
    for part in re.split(r'([A-Za-z_][A-Za-z0-9_./\\:+() ,\-]*[A-Za-z0-9_.)/])',value):
        if not part:continue
        run=p.add_run(part);run.font.name='Arial';run.font.size=Pt(12)
        run._element.get_or_add_rPr().append(OxmlElement('w:rtl'));run._element.rPr[-1].set(qn('w:val'),'0' if re.match('[A-Za-z_]',part) else '1')
        fonts=run._element.rPr.rFonts
        if fonts is not None:fonts.set(qn('w:cs'),'Arial')
def para(d,value,style=None):
    p=d.add_paragraph(style=style);direction(p);text(p,value);p.paragraph_format.space_after=Pt(8);p.paragraph_format.line_spacing=1.15;return p
def heading(d,title,level=1):
    p=d.add_heading(title,level);direction(p);p.paragraph_format.keep_with_next=True;return p
def step(d,number,title,body):
    p=para(d,f'{number}  {title}');p.runs[0].bold=True;p.paragraph_format.keep_with_next=True;para(d,body)
def image(d,name,caption,width=6.5):
    path=SHOTS/name
    if not path.exists():raise FileNotFoundError(path)
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(str(path),width=Inches(width));p.paragraph_format.keep_with_next=True
    p=para(d,caption);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:run.font.size=Pt(10);run.font.color.rgb=RGBColor.from_string('526175')
def page(d,title):d.add_page_break();heading(d,title)
def code(d,command):
    p=d.add_paragraph();direction(p,False);p.paragraph_format.space_after=Pt(8)
    run=p.add_run(command);run.font.name='Consolas';run.font.size=Pt(10.5)
def document(title,subtitle):
    d=Document();section=d.sections[0];section.page_width=Inches(8.5);section.page_height=Inches(11);section.left_margin=section.right_margin=Inches(.85);section.top_margin=Inches(.7);section.bottom_margin=Inches(.7)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
        style=d.styles[name];style.font.name='Arial';style.font.color.rgb=RGBColor(0,0,0);style.font.size=Pt(12 if name=='Normal' else 22 if name=='Title' else 16 if name=='Heading 1' else 13)
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:cs'),'Arial')
    d.styles['Normal'].paragraph_format.line_spacing=1.15
    d.core_properties.author=DEVELOPERS;d.core_properties.last_modified_by='NilePhytoDock Studio 0.3.0';d.core_properties.title=title
    header=section.header.paragraphs[0];header.text='NilePhytoDock Studio 0.3.0';header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:run.font.name='Arial';run.font.size=Pt(9);run.font.color.rgb=RGBColor(0,0,0)
    footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;footer.add_run('NilePhytoDock 0.3.0  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    p=d.add_paragraph(title,'Title');direction(p)
    para(d,subtitle,'Subtitle');para(d,'مطورو التطبيق: Ahmed G soliman و malak Taha')
    for style in d.styles:
        for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    return d
def simple_table(d,headers,records,widths):
    table=d.add_table(rows=1,cols=len(headers));table.autofit=False;flag(table._tbl.tblPr,'w:bidiVisual')
    borders=OxmlElement('w:tblBorders')
    for name in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+name);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    table._tbl.tblPr.append(borders)
    for cell,title,width in zip(table.rows[0].cells,headers,widths):
        cell.width=Inches(width);direction(cell.paragraphs[0]);text(cell.paragraphs[0],title)
        for run in cell.paragraphs[0].runs:run.bold=True
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F2F4F7');cell._tc.get_or_add_tcPr().append(shade)
    repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in records:
        for cell,value,width in zip(table.add_row().cells,values,widths):
            cell.width=Inches(width);p=cell.paragraphs[0];direction(p,not bool(re.match(r'^[A-Za-z][A-Za-z0-9_./\\ -]+$',value)));text(p,value)
            cell.vertical_alignment=1
            margins=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                margin=OxmlElement('w:'+side);margin.set(qn('w:w'),'100');margin.set(qn('w:type'),'dxa');margins.append(margin)
            cell._tc.get_or_add_tcPr().append(margins)
    return table
def equation(d,label,numerator,denominator):
    p=d.add_paragraph();direction(p,False);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    math=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=label+' = ';r.append(t);math.append(r)
    fraction=OxmlElement('m:f')
    for name,value in [('m:num',numerator),('m:den',denominator)]:
        part=OxmlElement(name);r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=value;r.append(t);part.append(r);fraction.append(part)
    math.append(fraction);p._p.append(math)

def user_guide():
    d=document('دليل تشغيل نايل فايتو دوك','خطوات عملية من فتح البرنامج إلى حفظ النتائج والتقارير')
    para(d,'هذا الدليل يشرح تشغيل النسخة المحمولة دون تثبيت Python أو Java أو أدوات docking منفصلة. اتبع الخطوات بالترتيب في أول دراسة، ثم استخدم أسماء الأزرار الإنجليزية الموضحة للوصول إلى كل وظيفة.')
    heading(d,'ابدأ من النسخة الصحيحة')
    step(d,'١','افتح الحزمة الجديدة','ادخل إلى مجلد NilePhytoDock Studio 0.3.0 وشغّل NilePhytoDock.exe أو الاختصار الموجود بجانبه. اترك مجلد _internal في مكانه. لا تستخدم ملفات EXE القديمة الموجودة في مجلدات التطوير.')
    step(d,'٢','تحقق من الجاهزية','انتظر شاشة البداية حتى تظهر الواجهة، ثم تأكد أن Engines available ظاهرة بالأعلى. تعرض Overview المكتبة ومسار العمل والدراسات السابقة. زر Quick guide يفتح هذا الدليل، وزر How the software was built يفتح دليل البناء والمنهج.')
    image(d,'overview.png','الشكل ١ الواجهة الفعلية للإصدار الجديد مع بيانات المكتبة المحلية')
    para(d,'المكتبة الحالية تضم ٢٩ بروفايلًا و٢٢٠ اسم مركب. يوجد ٤٦ سجلًا جاهزًا تمثل ٤٤ بنية كيميائية موثقة مختلفة، و١٧٤ اسمًا يحتاج مراجعة. عدد الأسماء ليس عدد الجزيئات الفريدة المؤكدة.')

    page(d,'استيراد البروتين وتجهيزه')
    step(d,'٣','استورد التركيب','افتح Protein targets ثم Import proteins. اختر ملف PDB أو mmCIF، ويمكن اختيار أكثر من ملف. يمكن أيضًا سحب الملفات إلى نافذة البرنامج. احتفظ باسم واضح لكل بروتين.')
    step(d,'٤','راجع معلومات التركيب','اختر صف البروتين واقرأ عدد السلاسل والبقايا والليجاندات والمعادن والتحذيرات. الملف الأصلي محفوظ كما هو؛ التجهيز ينشئ نسخة مستقلة. البروتين ذو عمود فقري ناقص يحتاج إصلاحًا خارجيًا قبل الحساب.')
    image(d,'targets.png','الشكل ٢ مراجعة البروتين المستورد قبل تشغيل التجهيز')
    step(d,'٥','اضبط تجهيز المستقبل','انتقل إلى Screening setup وافتح تبويب Receptor preparation. القيمة الافتراضية pH هي 7.4. احتفظ بالعوامل المساعدة والمعادن ما لم توجد مبررات علمية لإزالتها. اختيار الاحتفاظ بالماء قرار مرتبط بالدراسة.')
    para(d,'إذا كان الموقع مشغولًا بليجاند بلوري وتريد إعادة docking داخله، انقل اسم البقايا المحدد من معلومات البروتين إلى Remove bound residues. المثال التدريبي 3PTB يستخدم BEN A:1 فقط؛ هذا المثال لا يعني إزالة كل المركبات غير البروتينية من أي تركيب.')

    page(d,'توقع الجيوب ونقل الصندوق تلقائيًا')
    step(d,'٦','شغّل التوقع','بعد ضبط التجهيز اضغط Prepare & predict all proteins. ينفذ البرنامج التجهيز ثم P2Rank خارج خيط الواجهة، ويعرض مرحلة التنفيذ وأي خطأ. تغيير pH أو الماء أو قائمة الإزالة يبطل التوقعات القديمة ويستلزم إعادة هذه الخطوة.')
    step(d,'٧','اختر جيب كل بروتين','في Binding sites اختر البروتين من القائمة العلوية. أعلى جيب ترتيبًا يُختار تلقائيًا. يمكنك اختيار صف آخر ومراجعة احتماله ومركزه وبقاياه وصندوقه في العرض ثلاثي الأبعاد. استخدم Use selected pocket rank للعودة إلى الإعدادات.')
    image(d,'binding_sites.png','الشكل ٣ جيب حقيقي من P2Rank ومركزه وأبعاد البحث المحسوبة')
    para(d,'لا تنسخ قيم X أو Y أو Z يدويًا في الوضع التلقائي. يعرض جدول الإعدادات اختيارًا مستقلًا لكل بروتين، وينقل البرنامج القيم نفسها إلى Smina. أبعاد الصندوق مشتقة من ذرات بقايا الجيب مع هامش افتراضي ٦ أنجستروم؛ P2Rank لا يقيس هذه الأبعاد مباشرة.')
    para(d,'استخدم Custom box فقط عندما تريد تحديد المنطقة بنفسك، أو Reference ligand لبناء الصندوق حول ليجاند تجريبي معروف. فشل التوقع لا يستبدل المركز بصفر؛ يجب معالجة الرسالة أو اختيار وضع يدوي صريح.')

    page(d,'اختيار الزيوت وإعداد الحساب')
    step(d,'٨','حدد البروفايلات','افتح Oil library وضع علامة أمام البروفايل المطلوب. ابحث باسم النبات أو المركب. حافظ على الفصل بين المناطق وطرق الاستخلاص والمنتجات التجارية. HS بروفايل headspace وليس زيتًا مستخلصًا. المركبات غير الجاهزة تبقى مرئية لكنها لا تدخل الحساب.')
    step(d,'٩','حدد مكان النتائج','في Screening setup اختر Output Directory عبر Browse أو زر Output في شريط التشغيل الثابت. يمكنك إنشاء مجلد جديد أو استخدام المكان الافتراضي. يجري فحص الكتابة قبل إطلاق الحسابات، ويُنشأ اسم مشروع فريد لتجنب استبدال ملفات سابقة.')
    step(d,'١٠','راجع البروتوكول','افتح Docking protocol. القيم الافتراضية: exhaustiveness يساوي 8، وعدد poses يساوي 5، والبذرة 20261029، ومعالجان CPU. زيادة الجهد أو حجم الصندوق تزيد وقت الحساب. سجّل سبب تعديل الإعدادات وطبق بروتوكولًا متسقًا عند المقارنة.')
    image(d,'setup_protocol.png','الشكل ٤ تقسيم إعدادات الموقع والبروتوكول وتجهيز المستقبل إلى تبويبات')
    step(d,'١١','ابدأ وتابع','اضغط Run screening أو Start Screening. يعرض البرنامج مراحل التجهيز والتوقع وSmina وتحليل التفاعلات وحفظ التقارير. Pause يوقف الطابور بين الحسابات، بينما Cancel يوقف المحرك الحالي ويحفظ ما اكتمل. لا تعتبر نتيجة فاشلة درجة صفر.')

    page(d,'قراءة النتائج والتفاعلات')
    step(d,'١٢','افحص درجات الحساب','افتح Docking results. الدرجات بوحدة kcal/mol في دوال Vina المختارة؛ الدرجة الأكثر سلبية أفضل تنبؤيًا داخل البروتين والبروتوكول نفسيهما. لا تقارن الدرجات الخام بين بروتينين باعتبارها قياسًا مطلقًا للارتباط.')
    step(d,'١٣','افتح pose محددًا','انقر مرتين على صف محسوب لفتح Interactions. العرض ثلاثي الأبعاد يدعم التدوير والتكبير والتحريك، والرسم ثنائي الأبعاد يربط الذرات أو المجموعات الكيميائية الفعلية بالبقايا. استخدم Zoom وFit/reset وخيارات إظهار المسافات والأنواع والتسميات.')
    image(d,'interactions.png','الشكل ٥ تفاعلات فعلية مع ليجاند محسوب في العرضين ثلاثي وثنائي الأبعاد')
    para(d,'المسافات المكتوبة على الرسم مأخوذة من البنية ثلاثية الأبعاد بوحدة أنجستروم. طول الخط المرسوم ثنائي الأبعاد تخطيطي وليس مقياسًا للمسافة. الأحمر في ذرة الأكسجين لون عنصر كيميائي؛ نوع التفاعل يحدده لون الخط وتسميته.')
    para(d,'يمكن تصدير SVG وPNG بدقة 300 أو 600 DPI وملف PyMOL. تصدير 3D PNG يحفظ دقة نافذة العرض الحالية، وليس صورة ray tracing بدقة طباعة مستقلة.')

    page(d,'ترتيب الزيوت والتصدير واستعادة المشروع')
    step(d,'١٤','راجع الأولويات والتغطية','افتح Oil priorities. يعتمد المؤشر على رتب مركبات الزيت داخل كل بروتين وعلى نسبها المنشورة، وليس متوسط طاقات خام بين البروتينات. افحص تغطية المكونات والتحذيرات والحساسية. التغطية أقل من 70 نقطة مئوية تُعلَّم بأنها غير كافية.')
    para(d,'إذا ظهرت رسالة source review أو duplicate entries، يظل البروفايل موجودًا لكن مؤشره غير محسوب حتى مراجعة سجلاته. لا تُجمع السجلات المكررة ولا تُحذف تلقائيًا، وتستمر البروفايلات السليمة في الترتيب. لا تفسر قيمة غير متاحة على أنها صفر.')
    step(d,'١٥','احفظ وصدّر','التقارير التلقائية موجودة في Reports داخل مجلد الدراسة. من Reports أو Docking results يمكنك إنشاء حزمة PDF وDOCX وCSV وXLSX وSVG وPNG وJSON. الجداول المطبوعة تعرض أول ١٠٠ سجل لكل قسم، بينما CSV وXLSX يحتفظان بالبيانات الكاملة.')
    simple_table(d,['المجلد','المحتوى'],[('Proteins / Prepared_Proteins','الأصل ونسخة المستقبل المجهزة'),('P2Rank / Docking','توقعات الجيوب وأوامر Smina وملفات الحساب'),('Docked_Ligands / Complexes','الليجاندات والبنى المركبة'),('Interactions / 2D_Figures / 3D_Figures','التفاعلات والصور المصدرة'),('Heatmaps / Rankings / Reports / Logs','الرسوم والترتيب والتقارير والسجلات'),('Project_Data','ملف project.nile.sqlite وفهرس الملفات')],[2.7,3.9])
    step(d,'١٦','أعد فتح الدراسة','افتح Overview وانقر مرتين على دراسة سابقة، أو استخدم Open saved project واختر قاعدة SQLite المحفوظة. يفتح Open Results Folder مجلد الدراسة في Explorer. احتفظ بالمجلد كاملًا، وليس قاعدة البيانات وحدها، لأن الإحداثيات والصور ملفات مرتبطة بها.')

    page(d,'حل المشكلات المتكررة')
    for title,body in [
        ('زر التشغيل غير نشط','تحقق من اختيار زيت واحد على الأقل واستيراد بروتين، وجاهزية المحركات، ووجود بنى محلية جاهزة. في الوضع التلقائي يجب أن يكون لكل بروتين توقع جيب صالح بعد آخر تعديل للتجهيز.'),
        ('الأيقونة أو الواجهة تبدوان قديمتين','شغّل اختصار NilePhytoDock Studio 0.3 وافحص أن عنوان النافذة والإصدار هما 0.3.0. توجد ملفات تطوير أقدم؛ لا تشغّلها. الاختصار الجديد يشير صراحة إلى EXE والأيقونة داخل الحزمة الجديدة.'),
        ('المحرك فشل أو لم يظهر جيب','اقرأ التشخيص في الواجهة وملفات Logs. لا تُدخل إحداثيات عشوائية. راجع سلامة البروتين أو اختر صندوقًا يدويًا معللًا علميًا. نقص الذرات أو الكيمياء غير المدعومة يحتاج مراجعة.'),
        ('المجلد غير قابل للكتابة','اختر مجلدًا محليًا يمكن لحسابك الكتابة فيه، وافحص المساحة. تظل النتائج النهائية في الوجهة المحددة؛ الملفات المؤقتة للمحركات تُستخدم داخليًا فقط.'),
        ('الدرجات موجودة وبعض الزيوت بلا مؤشر','راجع التغطية والهويات غير المحسومة والتكرارات والتحذيرات. وجود docking ناجح لمركب لا يجعل كل بروفايل في المكتبة صالحًا لترتيب زيت كامل.'),
        ('أين أجد شرح البرمجة والمنهج','افتح BUILD_AND_METHOD_AR من مجلد Documentation أو زر How the software was built. يشرح الملفات والخوارزميات وطريقة البناء والاختبار وحدود التحقق.')]:
        heading(d,title,2);para(d,body)
    heading(d,'حدود الاستخدام العلمي',2);para(d,'هذه تنبؤات حسابية وليست قياسات ألفة أو دليلًا على نشاط بيولوجي أو تآزر خليط. تجهيز المستقبل لا يعيد بناء الحلقات أو السلاسل الجانبية الناقصة، ولا يحسب pKa خاصًا بالموقع أو مجموعة حالات بروتنة وتوتومرات لليجاند. تحقق مستقلًا قبل النشر أو الاستنتاج البيولوجي.')
    d.save(OUT/'USER_GUIDE_AR.docx')

def build_method():
    d=document('شرح بناء البرنامج والمنهج العلمي','كيف نُفّذ NilePhytoDock وما الذي يحسبه فعليًا وكيف يمكن إعادة بنائه')
    para(d,'يوثّق هذا الدليل مكونات التطبيق الموجود في المشروع، وليس تصميمًا افتراضيًا. الواجهة مكتبية أصلية، بينما عمليات التوقع وdocking وتحليل التفاعلات تنفذها محركات علمية حقيقية. لم يُستخدم PLIP، ولم تُزرع درجات تجريبية في قاعدة المكتبة.')
    heading(d,'الأدوات المستخدمة')
    simple_table(d,['المكون','استخدامه الفعلي'],[('Python 3.12.14 x64','ربط المكونات ومعالجة الملفات وقاعدة البيانات'),('PySide6 6.12.0','النوافذ والتبويبات والجداول والخيوط الخلفية وشاشة البداية'),('SQLite','المكتبة والمشروعات والجيوب والحسابات والتفاعلات وسجلات التنفيذ'),('P2Rank 2.5.1 / Java 17.0.19','توقع الجيوب عبر Java محلي مضمّن'),('Smina 2020.12.10','docking أصلي على Windows دون استبداله بمحرك آخر'),('RDKit 2026.09.1 / Meeko','التحقق الكيميائي والتحضير وإعادة ربط الذرات وملفات الليجاند'),('ProLIF 2.2.3 / OpenBabel','تصنيف التفاعلات وكيمياء الشحنات والتحويلات المساندة'),('3Dmol.js / matplotlib','عرض محلي ثلاثي الأبعاد ورسوم مشتقة من النتائج'),('python-docx / ReportLab / openpyxl','التقارير والجداول المصدرة'),('PyInstaller 6.22.3','تجميع EXE وحزمة الاعتماديات')],[2.65,3.95])
    para(d,'الإصدارات الدقيقة لكل الحزم مثبتة في requirements.txt. ملفات provenance والهاشات والتراخيص موجودة مع الأدوات الخارجية. مصدر Smina الموافق متاح في الحزمة، لكن ملفه الأصلي لم يُعَد بناؤه من المصدر خلال هذه الجلسة.')

    page(d,'تنظيم الكود ومسار التنفيذ')
    simple_table(d,['المسار','المسؤولية'],[('NilePhytoDock.py / app/main.py','مدخل التشغيل وهوية التطبيق وشاشة البداية ومعالجة أخطاء البدء'),('app/gui.py / app/redesign.py','الواجهة العلمية الأصلية وربط حقولها بالمعالجة'),('app/studio.py / app/flow_layout.py','شكل Studio والتبويبات والأزرار الملتفة والمساعدة'),('app/workers.py / scientific/runtime.py','QThread وتشغيل المحركات والإلغاء والمهل والسجلات'),('database/store.py / import_documents.py','المخطط والترحيلات ومحولات ملفات Word'),('database/import_csv.py','استيراد CSV مع مقارنة المصدر ومنع التكرار'),('scientific/proteins.py / ligands.py','التحضير والتحقق من البروتين والليجاند'),('scientific/pockets.py / docking.py','قراءة P2Rank وبناء الصناديق وتنفيذ Smina'),('scientific/interactions.py / ranking.py','تصنيف التفاعلات وحساب الأولويات والتغطية'),('scientific/pipeline.py / project_outputs.py','تسلسل العمل وحفظ الملفات والتقارير والمشروع'),('visualization / reporting','الرسم والعرض ثلاثي الأبعاد والتصدير')],[2.65,3.95])
    para(d,'كل عامل خلفي يفتح اتصال SQLite خاصًا به. تمرّر أوامر المحركات في قائمة arguments دون shell. تُحفظ حالة كل مهمة وملفاتها قبل الانتقال إلى التالية. يعمل طابور الحساب تسلسليًا مع تحكم في عدد خيوط Smina، لتظل الواجهة مستجيبة.')
    para(d,'التطبيق يفصل الموارد المضمّنة للقراءة عن البيانات القابلة للكتابة في LOCALAPPDATA. مسار نتائج الدراسة يختاره الباحث قبل التشغيل، وتُنشأ أسماء فريدة لمنع الاستبدال العرضي.')

    page(d,'بناء المكتبة والحفاظ على المصدر')
    para(d,'قُرئت ملفات Word السبعة بمحولات منفصلة لأن الجداول مختلفة. احتُفظ بالاسم الأصلي والصف والجدول والمرجع والنسبة والانحراف المعياري وحالة القيمة. فصلت البروفايلات بحسب المنطقة والطريقة والجزء النباتي والمنتج، ولم تتحول مجاميع الفئات الكيميائية إلى ليجاندات.')
    para(d,'بعد استيراد CSV المرفق أصبحت المكتبة ١١ نوعًا نباتيًا و٢٩ بروفايلًا و٢٢٠ اسم مركب و٦٦١ سجل تركيب أساسيًا. أضاف الملف ٤ بروفايلات و١٨ اسمًا و٦٤ قيمة أساسية. صفوفه الـ٥٨٣ تضم ٤٣٤ تطابقًا مؤيدًا و٨٥ اختلافًا محفوظًا للمراجعة؛ لم تستبدل الاختلافات قيم Word ولم تدخل كأوزان إضافية مكررة.')
    para(d,'تُحسب بصمة SHA256 للمصدر ويُحفظ الصف الأصلي في JSON. إعادة استيراد البايتات نفسها لا تضيف سجلات. النسب غير المحدودة أو غير الرقمية أو الواقعة خارج ٠ إلى ١٠٠ تُرفض قبل تعديل البيانات. الاختبارات قارنت السجلات الأصلية الـ٥٩٧ حقلًا بحقل بعد الاستيراد.')
    para(d,'مصدر البنى هو حل أسماء اختياري عبر PubChem مع فحص المرادفات وInChIKey وSMILES والتصاوغ في RDKit. لا يكفي أن تعيد الخدمة أي نتيجة. الهوية الغامضة أو التصاوغ غير المحسوم يبقيان للمراجعة. البنى الجاهزة مخزنة محليًا؛ لا يتطلب screening العادي تنزيلها مجددًا.')
    para(d,'التجهيز الآلي لليجاند يستخدم ETKDGv3 وبذرة 20261029، ثم MMFF94s أو UFF عندما تتوفر معلماته. يُرفض فشل التقارب أو الكيمياء غير الصالحة. يوجد ٤٦ سجلًا جاهزًا يمثل ٤٤ بنية مختلفة موثقة، و١٧٤ اسمًا غير جاهز؛ العدد ٢٢٠ ليس تأكيدًا لوجود ٢٢٠ مركبًا فريدًا.')

    page(d,'تجهيز البروتين ونقل جيب الارتباط')
    para(d,'يقرأ BioPython ملف PDB أو mmCIF. تُستخدم أول بنية نموذجية وأعلى إشغال للمواضع البديلة، مع خيارات صريحة للماء وإزالة بقايا بعينها. تُحفظ هندسة الذرات الثقيلة وتسمياتها؛ نقص العمود الفقري يؤدي إلى فشل ظاهر، ولا تُختلق حلقات أو سلاسل جانبية مفقودة.')
    para(d,'يتحقق RDKit من الرسم الكيميائي، وتُطبق قواعد بروتنة تقريبية للبقايا القياسية قبل إضافة الهيدروجين. هذه ليست تنبؤات pKa خاصة بالموقع. تُسند شحنات Gasteiger للجزء العضوي عبر OpenBabel، وتبقى العوامل المساعدة والمعادن بحاجة إلى مراجعة علمية.')
    para(d,'يُشغّل P2Rank الحقيقي عبر Java المضمّن، ثم تُقرأ ملفات predictions.csv حسب المجلد الناتج، مع إزالة الفراغات من العناوين والتحقق من أن مراكز الجيوب أعداد محدودة. تُحفظ الرتبة والدرجة والاحتمال والمركز والبقايا. لا توجد عودة صامتة إلى مركز صفري.')
    para(d,'يُحسب كل بُعد للصندوق حول مركز P2Rank بحيث يغطي أبعد ذرة ثقيلة في بقايا الجيب على ذلك المحور، ثم يضاف هامش ٦ أنجستروم لكل جانب، مع حد أدنى ١٢ وحد أقصى مدعوم ١٢٦ أنجستروم. المركز والصندوق مستقلان لكل بروتين.')
    para(d,'يربط البرنامج اختيار الجيب ببصمة ملف البروتين، ويبطل القيم القديمة بعد تغيير التجهيز. قارنت تجربة الواجهة على 3PTB و1IEP القيم المعروضة مع القيم الفعلية في أوامر Smina وقاعدة المشروع، دون إدخال الإحداثيات يدويًا.')
    para(d,'لعلاج مشاكل أسماء Unicode في بعض المكتبات الأصلية، يفتح Python الملفات كنصوص أو streams، وتعمل المحركات على نسخ متطابقة داخل مسار ASCII مؤقت. تُنسخ المخرجات إلى مجلد الدراسة المحدد، مع بقاء المسارات والسجلات والهاشات قابلة للمراجعة.')

    page(d,'الحساب وتصنيف التفاعلات والرسم')
    para(d,'يتلقى Smina المستقبل والليجاند والمركز والأبعاد ودالة scoring والجهد وعدد poses والبذرة وCPU. تُحفظ الإحداثيات والدرجات والمدة والإصدار والأمر الفعلي. يعتمد التخزين المؤقت على هاشات المدخلات والمحرك والإعدادات، وتُفحص ملفات النتائج قبل إعادة استخدامها.')
    para(d,'تُطابق ذرات pose مع قالب الليجاند الأصلي للحفاظ على ترتيب الروابط والتصاوغ المحدد، ثم يُعاد إنشاء complex مع تسميات المستقبل. لا تُستنتج الكيمياء فقط من مسافات PDBQT.')
    para(d,'يصنف ProLIF التفاعلات باستخدام هوية الذرات والكيمياء والهندسة. تشمل الفئات روابط الهيدروجين والتلامسات الكارهة للماء وVdW والشحنات والتكدس العطري المتوازي والمتعامد وتفاعلات الكاتيون مع الحلقة. التلامس القريب وحده ليس رابطة هيدروجينية.')
    para(d,'يحتاج الترابط المعدني إلى فلتر إضافي محافظ: غلاف Zn ثنائي التكافؤ رباعي السطوح أو Mg ثنائي التكافؤ ثماني السطوح كامل مع ذرات مانحة محددة كيميائيًا وحدود مسافات وزوايا موثقة في الكود. تُحذف هذه الفئة عندما يكون الغلاف ناقصًا أو المعدن غير مدعوم، دون اختلاق ترابط.')
    para(d,'الرسم ثنائي الأبعاد يستخدم إحداثيات RDKit المتجهية ويربط الخطوط بذرات الليجاند أو مركز مجموعته العطرية الفعلي. تُرتب تسميات البقايا قرب مناطق التلامس، ويتسع canvas لكثافة التسميات. يُعرض أقصر تلامس لكل بقايا ونوع عند التكرار، وتبقى كل التلامسات في الجدول.')
    para(d,'الرسم تخطيطي؛ أرقام المسافات من البنية ثلاثية الأبعاد ولا تعبر أطوال خطوطه عن المقياس الفيزيائي. يصدر SVG متجهيًا ويُرسم منه PNG عند 300 أو 600 DPI. العرض ثلاثي الأبعاد 3Dmol محلي داخل Qt WebEngine دون خادم أو CDN.')

    page(d,'ترتيب المركبات والزيوت وحدود الاستدلال')
    para(d,'لكل بروتين، تُؤخذ أفضل درجة لكل مركب من الجيوب والـposes المختارة. تتحول الدرجة إلى رتبة مئينية بين المركبات المحسوبة؛ أفضل مركب يأخذ ١ وأسوأها ٠، والتعادل يأخذ متوسط الرتب، والمركب الوحيد يأخذ ٠٫٥.')
    equation(d,'q','N - r','N - 1')
    para(d,'يرجح مؤشر الزيت هذه القيم بالنسب المنشورة للمكونات التي حُسبت بنجاح. تبقى النسب الأصلية في المصدر، ويعرض التقرير التغطية ومجموع النسب وفارق المكونات غير المتاحة. النسبة المنشورة مساحة قمة GC-MS وليست تلقائيًا كسرًا كتليًا.')
    equation(d,'Oil index','Σ wi qi','Σ wi')
    para(d,'إذا كان بروفايل يحوي سجلات مكررة لهوية مركب واحدة، يصبح مؤشر ذلك البروفايل غير متاح مع سبب واضح؛ لا تتضاعف الأوزان ولا تتوقف بقية البروفايلات السليمة. يُحتفظ بأفضل درجة مركب محسوبة عندما تتوفر، لكن ذلك لا يعوض غياب مؤشر زيت صالح.')
    para(d,'تغير الحساسية كل وفرة مشمولة بمقدار ١٠٪ زيادة أو نقصًا، واحدة في كل مرة. المقارنة متعددة الأهداف تجمع مؤشرات مطبّعة خاصة بكل هدف بأوزان صريحة، ولا تجمع الطاقات الخام بين بروتينات مختلفة. غياب هدف ذي وزن موجب يجعل المؤشر المشترك غير متاح.')
    para(d,'النتائج أدوات أولوية حسابية، وليست إثبات ألفة تجريبية أو سمية أو علاج أو تآزر خليط. حدود الهويات والتغطية والبروتنة وجودة المستقبل وعدد نظم التحقق تمنع تعميم دقة البحث على كل بروتين أو موقع معدني.')

    page(d,'إعادة البناء والتحقق من النسخة المحمولة')
    para(d,'المسار التالي للمطور فقط؛ المستخدم النهائي يشغّل EXE دون Python. على Windows x64 أنشئ بيئة Python 3.12 وثبّت requirements.txt. تحتفظ الحزمة بالأدوات الخارجية والنماذج وJava والليجاندات والبيانات والتراخيص.')
    code(d,'py -3.12 -m venv .venv')
    code(d,'.venv\\Scripts\\python.exe -m pip install -r requirements.txt')
    code(d,'.venv\\Scripts\\python.exe -m pytest -q')
    code(d,'powershell -File build\\build_windows.ps1')
    para(d,'يقرأ PyInstaller ملف build/NilePhytoDock.spec. يضمّن بيانات المكتبة والموارد ونسخ DLL المتوافقة، ويضيف الأيقونة وبيانات الإصدار من windows_version.txt. يعتمد التوزيع مجلدًا ذاتي الاحتواء لأن التجميع في ملف واحد أقل موثوقية لهذه الحزمة العلمية.')
    para(d,'الأيقونة مشتقة بصيغ ICO متعددة المقاسات من الصورة المرفقة دون إعادة رسم اللوجو. يُستخدم مسار أيقونة صريح في الاختصار وداخل Qt وموارد EXE، مع هوية تطبيق Windows للتجميع في شريط المهام. يجب فحص المسار والإصدار عند وجود نسخ تطوير قديمة.')
    para(d,'بعد البناء افتح EXE الناتج فعليًا من مجلد يحتوي مسافات، ثم نفذ دورة بروتين إلى P2Rank إلى Smina ثم التفاعلات والتقرير. نجاح كود المصدر أو أمر PyInstaller وحده لا يثبت نجاح الحزمة. سجل النسخة والهاشات وحالة الحسابات وملفات النتائج في بيان التحقق المصاحب.')
    heading(d,'أدلة الاختبار الفعلية',2)
    para(d,'اجتاز اختبار المصدر الآلي ٣٠ حالة قبل تجميع هذا الإصدار، مع تحذير deprecation واحد من MDAnalysis. نفذت الواجهة الجديدة ١٢ عملية فعلية على 3PTB و1IEP باستخدام ٦ مركبات من بروفايل Origanum، بينها Thymol وCarvacrol، مع مطابقة الصناديق وحفظ مشروع في مسار عربي وياباني وإعادة فتحه.')
    para(d,'حقق اختبار redocking المستقل لليجاند BEN في 3PTB قيمة RMSD للـpose الأعلى تقارب 0.394 أنجستروم، دون محاذاة لاحقة. نظام تحقق واحد لا يثبت معدل نجاح عام. اختبارات الهندسة المصطنعة تخص تصنيف التفاعلات ولا تُقدم كدرجات docking حقيقية.')
    para(d,'الأدلة موجودة في data/validation/pytest.log وscience/validation_results.json وstudio_workflow/validation.json وبيان التحقق من EXE. اختبارات Qt عند معاملات تكبير متعددة لا تعني اختبار كل إعدادات Windows الأصلية أو كل بطاقة رسومية. لم يُختبر Windows 10 أو VM نظيف، والملف غير موقّع.')
    heading(d,'تعديل التطبيق لاحقًا',2)
    para(d,'عدّل الشكل في app/studio.py، والهوية في app/branding.py، وخطوات المعالجة في scientific، ومحولات المصدر في database. أضف اختبارًا لأي تغيير علمي، ولا تعدل نسب المصدر أو تحسم تصاوغًا غامضًا لتسهيل التشغيل. راجع التراخيص والمصدر الموافق قبل توزيع نسخ عامة معدلة.')
    d.save(OUT/'BUILD_AND_METHOD_AR.docx')

if __name__=='__main__':
    OUT.mkdir(exist_ok=True);user_guide();build_method();print('Arabic user and development-method handbooks created')
