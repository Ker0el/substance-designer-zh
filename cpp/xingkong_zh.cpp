// xingkong_zh.cpp - 星空汉化 Substance 3D Designer 显示层引擎
// 只替换“绘制那一刻”的文本，不修改宿主控件、模型或工程数据。

#include <QApplication>
#include <QAbstractItemDelegate>
#include <QAbstractItemView>
#include <QChildEvent>
#include <QComboBox>
#include <QCoreApplication>
#include <QDialog>
#include <QFont>
#include <QFontMetrics>
#include <QGraphicsView>
#include <QHash>
#include <QIdentityProxyModel>
#include <QLabel>
#include <QLineEdit>
#include <QListView>
#include <QLocale>
#include <QMap>
#include <QPainter>
#include <QPlainTextEdit>
#include <QPointer>
#include <QSet>
#include <QStyledItemDelegate>
#include <QTextEdit>
#include <QThread>
#include <QTimer>
#include <QVariant>
#include <QVector>
#include <QWidget>

#include <windows.h>
#include <dbghelp.h>
#include <psapi.h>

#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <typeinfo>
#include <vector>

#define XK_EXPORT extern "C" __declspec(dllexport)

namespace {

constexpr int kApiVersion = 1;

LPTOP_LEVEL_EXCEPTION_FILTER g_previousExceptionFilter = nullptr;
bool g_crashFilterInstalled = false;

LONG WINAPI crashFilter(EXCEPTION_POINTERS *info) {
    wchar_t temp[MAX_PATH] = {};
    GetTempPathW(MAX_PATH, temp);
    wchar_t dumpPath[MAX_PATH] = {};
    swprintf_s(dumpPath, L"%sxingkong_crash_%lu.dmp", temp,
               GetCurrentProcessId());
    HANDLE file = CreateFileW(dumpPath, GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file != INVALID_HANDLE_VALUE) {
        MINIDUMP_EXCEPTION_INFORMATION exception{};
        exception.ThreadId = GetCurrentThreadId();
        exception.ExceptionPointers = info;
        exception.ClientPointers = FALSE;
        MiniDumpWriteDump(GetCurrentProcess(), GetCurrentProcessId(), file,
                          MiniDumpWithDataSegs, &exception, nullptr, nullptr);
        CloseHandle(file);
    }
    wchar_t textPath[MAX_PATH] = {};
    swprintf_s(textPath, L"%sxingkong_crash_%lu.txt", temp,
               GetCurrentProcessId());
    FILE *handle = nullptr;
    if (_wfopen_s(&handle, textPath, L"w") == 0 && handle) {
        const DWORD code = info && info->ExceptionRecord
                               ? info->ExceptionRecord->ExceptionCode : 0;
        const void *address = info && info->ExceptionRecord
                                  ? info->ExceptionRecord->ExceptionAddress
                                  : nullptr;
        fwprintf(handle, L"code=0x%08lX address=%p\n", code, address);
        fclose(handle);
    }
    if (g_previousExceptionFilter)
        return g_previousExceptionFilter(info);
    return EXCEPTION_EXECUTE_HANDLER;
}

void installCrashFilter() {
    if (g_crashFilterInstalled)
        return;
    g_previousExceptionFilter = SetUnhandledExceptionFilter(&crashFilter);
    g_crashFilterInstalled = true;
}

QHash<QString, QString> g_exact;
QHash<QString, QString> g_normalized;
QHash<QString, QString> g_idTranslations;
bool g_enabled = true;
bool g_fuzzy = true;
bool g_graph = false;

thread_local int g_paintDepth = 0;
thread_local qreal g_graphFontScale = 1.0;

bool onUiThread() {
    auto *app = qobject_cast<QApplication *>(QCoreApplication::instance());
    return app && QThread::currentThread() == app->thread();
}

bool containsHan(const QString &text) {
    for (const QChar ch : text) {
        const ushort u = ch.unicode();
        if ((u >= 0x3400 && u <= 0x4DBF) || (u >= 0x4E00 && u <= 0x9FFF) ||
            (u >= 0xF900 && u <= 0xFAFF))
            return true;
    }
    return false;
}

QString stripMnemonic(QString text) {
    text.replace(QStringLiteral("&&"), QStringLiteral("\x01"));
    text.remove(QLatin1Char('&'));
    text.replace(QStringLiteral("\x01"), QStringLiteral("&"));
    return text;
}

QString normalizeSource(QString text) {
    text = stripMnemonic(text);
    // 空白变体统一
    text.replace(QChar(0x00A0), QLatin1Char(' '));
    text.replace(QChar(0x2007), QLatin1Char(' '));
    text.replace(QChar(0x202F), QLatin1Char(' '));
    text.replace(QChar(0x3000), QLatin1Char(' '));
    text.replace(QLatin1Char('\r'), QLatin1Char('\n'));
    text = text.simplified();
    // 不可见字符
    text.remove(QChar(0x200B));
    text.remove(QChar(0x200C));
    text.remove(QChar(0x200D));
    text.remove(QChar(0xFEFF));
    text.remove(QChar(0x00AD));
    // 省略号与状态星号
    while (text.endsWith(QChar(0x2026)))
        text.chop(1);
    while (text.endsWith(QStringLiteral("...")))
        text.chop(3);
    if (text.endsWith(QStringLiteral(" *")))
        text.chop(2);
    text.replace(QLatin1Char('_'), QLatin1Char(' '));
    text = text.normalized(QString::NormalizationForm_C);
    // 全角 ASCII → 半角
    for (int i = 0; i < text.size(); ++i) {
        const ushort u = text.at(i).unicode();
        if (u >= 0xFF01 && u <= 0xFF5E)
            text[i] = QChar(ushort(u - 0xFEE0));
    }
    // 引号/破折号变体
    text.replace(QChar(0x2018), QLatin1Char('\''));
    text.replace(QChar(0x2019), QLatin1Char('\''));
    text.replace(QChar(0x201C), QLatin1Char('"'));
    text.replace(QChar(0x201D), QLatin1Char('"'));
    text.replace(QChar(0x2010), QLatin1Char('-'));
    text.replace(QChar(0x2011), QLatin1Char('-'));
    text.replace(QChar(0x2012), QLatin1Char('-'));
    text.replace(QChar(0x2013), QLatin1Char('-'));
    text.replace(QChar(0x2014), QLatin1Char('-'));
    text.replace(QChar(0x2015), QLatin1Char('-'));
    text = text.toCaseFolded();
    // 去变音符号（é → e）
    text = text.normalized(QString::NormalizationForm_D);
    QString stripped;
    stripped.reserve(text.size());
    for (const QChar ch : text) {
        const QChar::Category category = ch.category();
        if (category == QChar::Mark_NonSpacing ||
            category == QChar::Mark_SpacingCombining ||
            category == QChar::Mark_Enclosing)
            continue;
        stripped.append(ch);
    }
    stripped.remove(QLatin1Char(' '));
    return stripped.normalized(QString::NormalizationForm_C);
}

QString controlUniqueId(QWidget *widget, const QString &source) {
    if (!widget)
        return {};
    QWidget *parent = widget->parentWidget();
    const QString parentClass = parent
        ? QString::fromLatin1(parent->metaObject()->className())
        : QStringLiteral("None");
    const QString selfClass = QString::fromLatin1(widget->metaObject()->className());
    const QString objectName = widget->objectName().isEmpty()
        ? QStringLiteral("None") : widget->objectName();
    return parentClass + QStringLiteral("||") + selfClass +
           QStringLiteral("||") + objectName + QStringLiteral("||") + source;
}

bool looksTranslatable(const QString &text) {
    const QString t = text.trimmed();
    if (t.isEmpty() || t.size() > 200 || containsHan(t))
        return false;
    if (t.contains(QStringLiteral("://")) || t.contains(QLatin1Char('/')) ||
        t.contains(QLatin1Char('\\')))
        return false;
    for (const QChar ch : t) {
        if (ch.isLetter())
            return true;
    }
    return false;
}

QString translateText(const QString &source, QWidget *widget) {
    if (!g_enabled)
        return {};
    QString key = source.trimmed();
    if (key.isEmpty())
        return {};

    // 1. 控件 ID 专项词库优先（解决同名原文在不同位置要不同译法）。
    if (!g_idTranslations.isEmpty() && widget) {
        const QString id = controlUniqueId(widget, key);
        auto idHit = g_idTranslations.constFind(id);
        if (idHit != g_idTranslations.constEnd()) {
            if (idHit.value() == QStringLiteral("_skip_"))
                return {};
            return idHit.value();
        }
        // 通配 _skip_：上级类名||自身类名||objectName||*
        int separator = -2;
        for (int part = 0; part < 3; ++part) {
            separator = id.indexOf(QStringLiteral("||"), separator + 2);
            if (separator < 0)
                break;
        }
        if (separator > 0) {
            const QString wildcard = id.left(separator) + QStringLiteral("||*");
            if (g_idTranslations.value(wildcard) == QStringLiteral("_skip_"))
                return {};
            if (g_exact.value(wildcard) == QStringLiteral("_skip_"))
                return {};
        }
    }

    // Designer 在实例参数被覆盖后追加 " *"；保留这个状态标记。
    QString suffix;
    if (key.endsWith(QLatin1Char('*'))) {
        key.chop(1);
        key = key.trimmed();
        suffix = QStringLiteral(" *");
    }

    auto exact = g_exact.constFind(key);
    if (exact != g_exact.constEnd())
        return exact.value() + suffix;

    const QString stripped = stripMnemonic(key);
    if (stripped != key) {
        exact = g_exact.constFind(stripped);
        if (exact != g_exact.constEnd())
            return exact.value() + suffix;
    }

    if (containsHan(key) || !looksTranslatable(key))
        return {};

    if (g_fuzzy) {
        const QString norm = normalizeSource(key);
        if (norm.size() >= 2) {
            auto ni = g_normalized.constFind(norm);
            if (ni != g_normalized.constEnd())
                return ni.value() + suffix;
        }
    }
    return {};
}

class XingKongDelegate final : public QStyledItemDelegate {
public:
    explicit XingKongDelegate(QObject *parent = nullptr)
        : QStyledItemDelegate(parent) {}

    QString displayText(const QVariant &value, const QLocale &locale) const override {
        const QString text = QStyledItemDelegate::displayText(value, locale);
        if (!g_enabled)
            return text;
        auto *widget = qobject_cast<QWidget *>(parent());
        const QString translated = translateText(text, widget);
        return translated.isEmpty() ? text : translated;
    }
};

struct DelegateBinding {
    QPointer<QAbstractItemView> view;
    QStyledItemDelegate *original = nullptr;
    XingKongDelegate *ours = nullptr;
};

QVector<DelegateBinding> g_bindings;

[[maybe_unused]] void installCustomViewDelegate(QAbstractItemView *view);

// 宿主对话框（首选项、新建 Substance 图形）内部的列表由宿主自己管理绘制与编辑。
// 插件在这些窗口里不接管 delegate，避免顶掉宿主自绘的快捷键输入框/模板缩略图；
// 对话框文字仍由 QPainter::drawText 钩子翻译。
bool insideHostDialog(QWidget *widget) {
    for (QWidget *p = widget; p; p = p->parentWidget()) {
        if (qobject_cast<QDialog *>(p))
            return true;
        const QString cls = QString::fromLatin1(p->metaObject()->className());
        if (cls.contains(QStringLiteral("SettingsEditor")) ||
            cls.contains(QStringLiteral("NewSubstanceDialog")) ||
            cls.contains(QStringLiteral("NewGraphImpl")))
            return true;
    }
    return false;
}

void installViewDelegate(QAbstractItemView *view) {
    if (!view)
        return;
    {
        const char *temp = std::getenv("TEMP");
        const std::string path =
            std::string(temp ? temp : ".") + "\\xingkong_view.log";
        std::ofstream out(path, std::ios::app);
        if (out) {
            out << "view=" << view->metaObject()->className()
                << " model="
                << (view->model() ? view->model()->metaObject()->className()
                                  : "null")
                << " delegate="
                << (view->itemDelegate()
                        ? view->itemDelegate()->metaObject()->className()
                        : "null")
                << "\n";
        }
    }
    for (auto it = g_bindings.begin(); it != g_bindings.end();) {
        if (it->view == view) {
            // 宿主切换分类/模型时可能重新 setItemDelegate，旧登记要作废。
            if (it->ours && view->itemDelegate() == it->ours)
                return;
            it = g_bindings.erase(it);
        } else {
            ++it;
        }
    }
    auto *rawDelegate = view->itemDelegate();
    if (!rawDelegate)
        return;
    if (insideHostDialog(view))
        return;
    // 只替换 RTTI 精确为 QStyledItemDelegate 的实例。宿主大量使用没有 Q_OBJECT
    // 的 QStyledItemDelegate 子类，metaObject() 会把它们误报成基类；一旦替换，
    // 宿主自定义的绘制/编辑（快捷键输入框、模板缩略图）就会丢失。
    if (typeid(*rawDelegate) != typeid(QStyledItemDelegate))
        return;
    auto *delegate = qobject_cast<QStyledItemDelegate *>(rawDelegate);
    if (!delegate)
        return;
    auto *ours = new XingKongDelegate(view);
    // 先登记再 setItemDelegate：Qt 可能在切换 delegate 时同步发出
    // Polish/ChildAdded，事件过滤器会重入这里的扫描。
    g_bindings.push_back({QPointer<QAbstractItemView>(view), delegate, ours});
    view->setItemDelegate(ours);
}

void installComboDelegate(QComboBox *combo);
void installCustomViewDelegate(QAbstractItemView *view);
void installComboForView(QAbstractItemView *view);

void scanWidgetTree(QWidget *widget) {
    static thread_local int scanDepth = 0;
    if (!widget || scanDepth > 4)
        return;
    struct DepthGuard {
        int &depth;
        explicit DepthGuard(int &value) : depth(value) { ++depth; }
        ~DepthGuard() { --depth; }
    } guard(scanDepth);
    if (auto *view = qobject_cast<QAbstractItemView *>(widget)) {
        installViewDelegate(view);
        installComboForView(view);
    }
    if (auto *combo = qobject_cast<QComboBox *>(widget))
        installComboDelegate(combo);
    const auto views = widget->findChildren<QAbstractItemView *>();
    for (auto *view : views)
        installViewDelegate(view);
    const auto combos = widget->findChildren<QComboBox *>();
    for (auto *combo : combos)
        installComboDelegate(combo);
}

void restoreDelegates() {
    for (const auto &binding : g_bindings) {
        if (!binding.view)
            continue;
        if (binding.ours && binding.view->itemDelegate() == binding.ours)
            binding.view->setItemDelegate(binding.original);
        delete binding.ours;
    }
    g_bindings.clear();
}

// ---------------------------------------------------------------------------
// 下拉框：包装宿主原有 delegate，只把 DisplayRole 换成译文。
// 交互、选中、图标、分组样式仍走原 delegate；真实 model 不被改写。
// ---------------------------------------------------------------------------
class ComboProxyModel final : public QIdentityProxyModel {
public:
    ComboProxyModel(QWidget *context, QObject *parent)
        : QIdentityProxyModel(parent), context_(context) {}

    bool setData(const QModelIndex &, const QVariant &, int) override { return false; }
    bool setItemData(const QModelIndex &, const QMap<int, QVariant> &) override { return false; }

    QVariant data(const QModelIndex &index,
                  int role = Qt::DisplayRole) const override {
        const QVariant value = QIdentityProxyModel::data(index, role);
        if (role != Qt::DisplayRole || !g_enabled || !context_)
            return value;
        const QString source = value.toString();
        const QString target = translateText(source, context_);
        return target.isEmpty() ? value : QVariant(target);
    }

private:
    QPointer<QWidget> context_;
};

class XingKongComboDelegate final : public QAbstractItemDelegate {
public:
    XingKongComboDelegate(QAbstractItemView *view, QWidget *context,
                          QAbstractItemDelegate *original)
        : QAbstractItemDelegate(view), original_(original),
          proxy_(context, this), fallback_(this) {
        if (original) {
            connect(original, &QAbstractItemDelegate::commitData,
                    this, &QAbstractItemDelegate::commitData);
            connect(original, &QAbstractItemDelegate::closeEditor,
                    this, &QAbstractItemDelegate::closeEditor);
            connect(original, &QAbstractItemDelegate::sizeHintChanged,
                    this, &QAbstractItemDelegate::sizeHintChanged);
        }
    }

    void paint(QPainter *painter, const QStyleOptionViewItem &option,
               const QModelIndex &index) const override {
        if (!index.isValid())
            return;
        ensureSourceModel(index.model());
        originalDelegate()->paint(painter, option, proxy_.mapFromSource(index));
    }

    QSize sizeHint(const QStyleOptionViewItem &option,
                   const QModelIndex &index) const override {
        if (!index.isValid())
            return {};
        ensureSourceModel(index.model());
        return originalDelegate()->sizeHint(option, proxy_.mapFromSource(index));
    }

    QWidget *createEditor(QWidget *parent, const QStyleOptionViewItem &option,
                          const QModelIndex &index) const override {
        return originalDelegate()->createEditor(parent, option, index);
    }
    void destroyEditor(QWidget *editor, const QModelIndex &index) const override {
        originalDelegate()->destroyEditor(editor, index);
    }
    void setEditorData(QWidget *editor, const QModelIndex &index) const override {
        originalDelegate()->setEditorData(editor, index);
    }
    void setModelData(QWidget *editor, QAbstractItemModel *model,
                      const QModelIndex &index) const override {
        originalDelegate()->setModelData(editor, model, index);
    }
    void updateEditorGeometry(QWidget *editor, const QStyleOptionViewItem &option,
                              const QModelIndex &index) const override {
        originalDelegate()->updateEditorGeometry(editor, option, index);
    }
    bool editorEvent(QEvent *event, QAbstractItemModel *model,
                     const QStyleOptionViewItem &option,
                     const QModelIndex &index) override {
        return originalDelegate()->editorEvent(event, model, option, index);
    }
    bool helpEvent(QHelpEvent *event, QAbstractItemView *view,
                   const QStyleOptionViewItem &option,
                   const QModelIndex &index) override {
        return originalDelegate()->helpEvent(event, view, option, index);
    }

private:
    QAbstractItemDelegate *originalDelegate() const {
        return original_ ? original_.data() : &fallback_;
    }
    void ensureSourceModel(const QAbstractItemModel *model) const {
        if (model && proxy_.sourceModel() != model)
            proxy_.setSourceModel(const_cast<QAbstractItemModel *>(model));
    }

    QPointer<QAbstractItemDelegate> original_;
    mutable ComboProxyModel proxy_;
    mutable QStyledItemDelegate fallback_;
};

struct ComboBinding {
    QPointer<QAbstractItemView> view;
    QPointer<QAbstractItemDelegate> original;
    QPointer<XingKongComboDelegate> ours;
};

QVector<ComboBinding> g_comboBindings;

bool isSafeComboDelegate(QAbstractItemDelegate *delegate) {
    if (!delegate)
        return false;
    const QByteArray name = delegate->metaObject()->className();
    // 只包装 Qt 标准下拉 delegate。Adobe 自定义 delegate 可能假定
    // index.model() 是它自己的模型；塞入 identity proxy 会越界/崩溃。
    return name == "QComboBoxDelegate" || name == "QComboMenuDelegate" ||
           name == "QStyledItemDelegate" || name == "QItemDelegate";
}

void installComboDelegate(QComboBox *combo) {
    if (!combo || !combo->view() || QCoreApplication::closingDown())
        return;
    auto *view = combo->view();
    for (auto it = g_comboBindings.begin(); it != g_comboBindings.end();) {
        if (it->view == view) {
            if (it->ours && view->itemDelegate() == it->ours)
                return;
            it = g_comboBindings.erase(it);
        } else {
            ++it;
        }
    }
    auto *original = view->itemDelegate();
    if (!isSafeComboDelegate(original))
        return;
    auto *ours = new XingKongComboDelegate(view, combo, original);
    g_comboBindings.push_back({QPointer<QAbstractItemView>(view),
                               QPointer<QAbstractItemDelegate>(original), ours});
    view->setItemDelegate(ours);
    if (view->viewport())
        view->viewport()->update();
}

void restoreComboDelegates() {
    for (auto it = g_comboBindings.rbegin(); it != g_comboBindings.rend(); ++it) {
        if (!it->view)
            continue;
        if (it->ours && it->view->itemDelegate() == it->ours) {
            if (it->original)
                it->view->setItemDelegate(it->original);
            else
                it->view->setItemDelegate(new QStyledItemDelegate(it->view));
        }
        delete it->ours;
    }
    g_comboBindings.clear();
}

void installComboForView(QAbstractItemView *view) {
    if (!view)
        return;
    for (auto *widget : QApplication::allWidgets()) {
        if (auto *combo = qobject_cast<QComboBox *>(widget)) {
            if (combo->view() == view) {
                installComboDelegate(combo);
                return;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Designer 资源架 / 库树使用自定义 delegate；包装原 delegate，
// 用 identity proxy 只替换 DisplayRole，这样官方中文也能被覆盖。
// ---------------------------------------------------------------------------
QVector<ComboBinding> g_viewBindings;

bool isDesignerResourceView(QAbstractItemView *view) {
    if (!view)
        return false;
    const QString viewClass =
        QString::fromLatin1(view->metaObject()->className());
    const QString modelClass = view->model()
        ? QString::fromLatin1(view->model()->metaObject()->className())
        : QString();
    return viewClass.endsWith(QStringLiteral("CustomListView")) ||
           viewClass.endsWith(QStringLiteral("LibraryTree")) ||
           viewClass.contains(QStringLiteral("Resource")) ||
           viewClass.contains(QStringLiteral("Library")) ||
           modelClass.endsWith(QStringLiteral("ResourcesListModel")) ||
           modelClass.contains(QStringLiteral("Resource")) ||
           modelClass.contains(QStringLiteral("Asset"));
}

[[maybe_unused]] void installCustomViewDelegate(QAbstractItemView *view) {
    if (!view || QCoreApplication::closingDown())
        return;
    const QString viewClass =
        QString::fromLatin1(view->metaObject()->className());
    const QString modelClass = view->model()
        ? QString::fromLatin1(view->model()->metaObject()->className())
        : QString();
    if (viewClass.contains(QStringLiteral("Resource")) ||
        viewClass.contains(QStringLiteral("Library")) ||
        modelClass.contains(QStringLiteral("Resource"))) {
        const char *temp = std::getenv("TEMP");
        const std::string path =
            std::string(temp ? temp : ".") + "\\xingkong_view.log";
        std::ofstream out(path, std::ios::app);
        if (out) {
            out << "check view=" << viewClass.toUtf8().constData()
                << " model=" << modelClass.toUtf8().constData()
                << " delegate="
                << (view->itemDelegate()
                        ? view->itemDelegate()->metaObject()->className()
                        : "null")
                << " matched=" << isDesignerResourceView(view) << "\n";
        }
    }
    if (!isDesignerResourceView(view))
        return;
    for (auto it = g_viewBindings.begin(); it != g_viewBindings.end();) {
        if (it->view == view) {
            if (it->ours && view->itemDelegate() == it->ours)
                return;
            it = g_viewBindings.erase(it);
        } else {
            ++it;
        }
    }
    auto *original = view->itemDelegate();
    if (!original)
        return;
    if (QString::fromLatin1(original->metaObject()->className()) ==
        QStringLiteral("QComboBoxDelegate"))
        return;
    auto *ours = new XingKongComboDelegate(view, view, original);
    g_viewBindings.push_back({QPointer<QAbstractItemView>(view),
                              QPointer<QAbstractItemDelegate>(original), ours});
    view->setItemDelegate(ours);
    if (view->viewport())
        view->viewport()->update();
}

void restoreCustomViewDelegates() {
    for (auto it = g_viewBindings.rbegin(); it != g_viewBindings.rend(); ++it) {
        if (!it->view)
            continue;
        if (it->ours && it->view->itemDelegate() == it->ours) {
            if (it->original)
                it->view->setItemDelegate(it->original);
            else
                it->view->setItemDelegate(new QStyledItemDelegate(it->view));
        }
        delete it->ours;
    }
    g_viewBindings.clear();
}

void observeSearchWidget(QWidget *widget);

class XingKongFilter final : public QObject {
public:
    using QObject::QObject;

    bool eventFilter(QObject *watched, QEvent *event) override {
        const auto type = event->type();
        if (type == QEvent::ChildAdded) {
            if (auto *child = qobject_cast<QWidget *>(
                    static_cast<QChildEvent *>(event)->child())) {
                scanWidgetTree(child);
                observeSearchWidget(child);
            }
        } else if (type == QEvent::Polish || type == QEvent::Show) {
            if (auto *widget = qobject_cast<QWidget *>(watched)) {
                scanWidgetTree(widget);
                observeSearchWidget(widget);
            }
        }
        return false;
    }
};

QPointer<XingKongFilter> g_filter;

// ---------------------------------------------------------------------------
// 资源架中英搜索：中文查询时暂时接管过滤（隐藏不匹配行），英文查询保持宿主原生搜索。
// ---------------------------------------------------------------------------
class ResourceSearchFilter final : public QObject {
public:
    explicit ResourceSearchFilter(QObject *parent = nullptr)
        : QObject(parent), timer_(new QTimer(this)) {
        timer_->setSingleShot(true);
        timer_->setInterval(40);
        connect(timer_, &QTimer::timeout, this, [this] { apply(); });
    }

    void observe(QWidget *widget) {
        if (QCoreApplication::closingDown())
            return;
        QWidget *container = resourceContainer(widget);
        if (!container)
            return;
        if (container_ == container && field_ && view_ && view_->model() == model_)
            return;
        bind(container);
    }

    void setActive(bool active) {
        active_ = active;
        if (!active_) {
            restore();
            local_ = false;
            query_.clear();
        } else if (field_ && containsHan(field_->text())) {
            onTextChanged(field_->text());
        }
    }

    void refresh() {
        if (active_ && local_)
            timer_->start();
    }

    void shutdown() {
        active_ = false;
        restore();
        disconnectAll();
        field_ = nullptr;
        view_ = nullptr;
        model_ = nullptr;
        container_ = nullptr;
    }

private:
    static QString className(const QObject *object) {
        return object ? QString::fromLatin1(object->metaObject()->className())
                      : QString();
    }

    static QWidget *resourceContainer(QWidget *widget) {
        int depth = 0;
        for (QObject *current = widget; current && depth < 14;
             current = current->parent(), ++depth) {
            if (className(current) == QStringLiteral("Pfx::DataBase::ResourceTableWidget"))
                return qobject_cast<QWidget *>(current);
        }
        return nullptr;
    }

    void bind(QWidget *container) {
        if (QCoreApplication::closingDown() || binding_)
            return;
        struct FlagGuard {
            bool &flag;
            explicit FlagGuard(bool &value) : flag(value) { flag = true; }
            ~FlagGuard() { flag = false; }
        } guard(binding_);
        disconnectAll();
        restore();
        container_ = container;
        field_ = container->findChild<QLineEdit *>(QStringLiteral("globalSearch"));
        if (!field_) {
            for (auto *candidate : container->findChildren<QLineEdit *>()) {
                if (candidate->objectName() == QStringLiteral("globalSearch")) {
                    field_ = candidate;
                    break;
                }
            }
        }
        view_ = nullptr;
        for (auto *candidate : container->findChildren<QListView *>()) {
            if (className(candidate).endsWith(QStringLiteral("CustomListView"))) {
                view_ = candidate;
                break;
            }
        }
        if (!view_)
            view_ = container->findChild<QListView *>();
        if (!field_ || !view_ || !view_->model())
            return;
        model_ = view_->model();
        conns_.push_back(connect(field_, &QLineEdit::textChanged, this,
                                 [this](const QString &text) { onTextChanged(text); }));
        conns_.push_back(connect(model_, &QAbstractItemModel::modelReset, this,
                                 [this] { hidden_.clear(); if (active_ && local_) timer_->start(); }));
        conns_.push_back(connect(model_, &QAbstractItemModel::rowsInserted, this,
                                 [this](const QModelIndex &, int, int) { if (active_ && local_) timer_->start(); }));
        conns_.push_back(connect(model_, &QAbstractItemModel::rowsRemoved, this,
                                 [this](const QModelIndex &, int, int) {
                                     // 行删除过程中不能回写 setRowHidden，索引可能已失效。
                                     hidden_.clear();
                                     if (active_ && local_) timer_->start();
                                 }));
        conns_.push_back(connect(model_, &QAbstractItemModel::layoutChanged, this,
                                 [this] { if (active_ && local_) timer_->start(); }));
        if (active_ && containsHan(field_->text()))
            onTextChanged(field_->text());
    }

    void disconnectAll() {
        for (const auto &connection : conns_)
            disconnect(connection);
        conns_.clear();
    }

    void onTextChanged(const QString &text) {
        if (!active_ || applying_ || !field_ || !view_)
            return;
        if (containsHan(text)) {
            local_ = true;
            query_ = text.trimmed();
            // 让宿主先回到完整列表，再叠加本地中文过滤；不改用户输入内容。
            applying_ = true;
            QMetaObject::invokeMethod(field_, "textChanged", Qt::DirectConnection,
                                      Q_ARG(QString, QString()));
            applying_ = false;
            timer_->start();
        } else {
            restore();
            local_ = false;
            query_.clear();
        }
    }

    void apply() {
        if (QCoreApplication::closingDown() || filtering_)
            return;
        filtering_ = true;
        struct ResetFlag {
            bool &flag;
            ~ResetFlag() { flag = false; }
        } reset{filtering_};
        if (!active_ || !local_ || !view_ || !model_)
            return;
        if (view_->model() != model_) {
            restore();
            bind(container_);
            return;
        }
        QStringList terms;
        for (const QString &word : query_.simplified().split(QLatin1Char(' '))) {
            const QString normalized = normalizeSource(word);
            if (!normalized.isEmpty())
                terms.append(normalized);
        }
        if (terms.isEmpty()) {
            restore();
            return;
        }
        const int rows = model_->rowCount();
        for (int row = 0; row < rows; ++row) {
            const QString source =
                model_->index(row, 0).data(Qt::DisplayRole).toString().trimmed();
            const QString target = translateText(source, view_);
            const QString combined = normalizeSource(source + QLatin1Char(' ') + target);
            bool match = true;
            for (const QString &term : terms) {
                if (!combined.contains(term)) {
                    match = false;
                    break;
                }
            }
            if (match) {
                if (hidden_.contains(row)) {
                    view_->setRowHidden(row, false);
                    hidden_.remove(row);
                }
            } else if (!hidden_.contains(row)) {
                view_->setRowHidden(row, true);
                hidden_.insert(row);
            }
        }
    }

    void restore() {
        // 只有 model 仍是绑定时的那一个才回写；切分类/重建模型时旧行号已失效。
        if (view_ && model_ && view_->model() == model_) {
            for (int row : hidden_)
                view_->setRowHidden(row, false);
        }
        hidden_.clear();
    }

    QPointer<QWidget> container_;
    QPointer<QLineEdit> field_;
    QPointer<QListView> view_;
    QPointer<QAbstractItemModel> model_;
    QVector<QMetaObject::Connection> conns_;
    QTimer *timer_ = nullptr;
    QSet<int> hidden_;
    QString query_;
    bool local_ = false;
    bool applying_ = false;
    bool binding_ = false;
    bool filtering_ = false;
    bool active_ = true;
};

QPointer<ResourceSearchFilter> g_searchFilter;

void observeSearchWidget(QWidget *widget) {
    if (g_searchFilter)
        g_searchFilter->observe(widget);
}

using DrawPoint = void (*)(QPainter *, const QPoint &, const QString &);
using DrawPointF = void (*)(QPainter *, const QPointF &, const QString &);
using DrawPointF2 = void (*)(QPainter *, const QPointF &, const QString &, int, int);
using DrawRect = void (*)(QPainter *, const QRect &, int, const QString &, QRect *);
using DrawRectFOption = void (*)(QPainter *, const QRectF &, const QString &,
                                 const QTextOption &);
using DrawRectFAlign = void (*)(QPainter *, const QRectF &, int,
                                const QString &, QRectF *);
using DrawXY = void (*)(QPainter *, int, int, const QString &);
using DrawXYWH = void (*)(QPainter *, int, int, int, int, int,
                          const QString &, QRect *);

DrawPoint g_drawPoint = nullptr;
DrawPointF g_drawPointF = nullptr;
DrawPointF2 g_drawPointF2 = nullptr;
DrawRect g_drawRect = nullptr;
DrawRectFOption g_drawRectFOption = nullptr;
DrawRectFAlign g_drawRectFAlign = nullptr;
DrawXY g_drawXY = nullptr;
DrawXYWH g_drawXYWH = nullptr;

struct HookSlot {
    void **slot = nullptr;
    void *original = nullptr;
    void *replacement = nullptr;
};

std::vector<HookSlot> g_slots;
std::vector<HMODULE> g_moduleRefs;
std::atomic<int> g_activeCalls{0};
bool g_hooksInstalled = false;

class CallScope {
public:
    CallScope() { ++g_activeCalls; }
    ~CallScope() { --g_activeCalls; }
};

class PaintFontGuard {
public:
    explicit PaintFontGuard(QPainter *painter)
        : painter_(painter), oldFont_(painter ? painter->font() : QFont()) {
        if (painter_ && g_graphFontScale < 0.999) {
            QFont font = oldFont_;
            if (font.pixelSize() > 0)
                font.setPixelSize(qMax(6, int(font.pixelSize() * g_graphFontScale)));
            else if (font.pointSizeF() > 0.0)
                font.setPointSizeF(qMax(4.0, font.pointSizeF() * g_graphFontScale));
            painter_->setFont(font);
        }
    }
    ~PaintFontGuard() {
        if (painter_ && g_graphFontScale < 0.999)
            painter_->setFont(oldFont_);
    }

private:
    QPainter *painter_ = nullptr;
    QFont oldFont_;
};

bool isDesignerGraphViewport(QWidget *owner) {
    if (!owner)
        return false;
    auto *view = qobject_cast<QGraphicsView *>(owner->parentWidget());
    if (!view)
        return false;
    const QString className = QString::fromLatin1(view->metaObject()->className());
    return className == QStringLiteral("Pfx::Editor::Components::Graph::GraphView") ||
           className.endsWith(QStringLiteral("::GraphView"));
}

QString translateForPainter(QPainter *painter, const QString &text,
                            const QRectF *rect = nullptr) {
    g_graphFontScale = 1.0;
    // QPainter::drawText 也可能由渲染/后台线程调用；非 GUI 线程不碰 QWidget、
    // 也不读正在构建的词库（否则会与启动时的 4168 条 push 竞争）。
    if (!onUiThread() || !g_enabled || g_paintDepth > 0 || !painter || text.isEmpty())
        return {};
    QWidget *owner = dynamic_cast<QWidget *>(painter->device());
    if (!owner)
        return {}; // 离屏 QImage/QPixmap/打印：绝不翻译，避免污染导出
    const QString source = text.trimmed();
    if (source.isEmpty())
        return {};
    if (auto *edit = qobject_cast<QLineEdit *>(owner)) {
        // 只翻 placeholder，用户输入的内容永远保持原文。
        if (!edit->text().isEmpty())
            return {};
        if (edit->placeholderText().trimmed() != source)
            return {};
    }
    if (qobject_cast<QTextEdit *>(owner) || qobject_cast<QPlainTextEdit *>(owner))
        return {}; // 文档内容不翻
    QString target = translateText(source, owner);
    if (target.isEmpty())
        return {};
    if (isDesignerGraphViewport(owner)) {
        // 点坐标绘制的节点标题没有裁剪矩形，正常翻译；
        // 有矩形/裁剪区域时按实际可用宽度判断，放不下就保留英文，避免半截字。
        const QFontMetrics metrics(painter->font());
        const int targetWidth = metrics.horizontalAdvance(target);
        const QRectF clip = painter->clipBoundingRect();
        if (source.contains(QStringLiteral("Background")) ||
            source.contains(QStringLiteral("Main")) ||
            source.contains(QStringLiteral("Back")) ||
            target.contains(QStringLiteral("背"))) {
            const char *temp = std::getenv("TEMP");
            const std::string path =
                std::string(temp ? temp : ".") + "\\xingkong_graph.log";
            std::ofstream out(path, std::ios::app);
            if (out) {
                out << "src=" << source.toUtf8().constData()
                    << " | dst=" << target.toUtf8().constData()
                    << " | targetWidth=" << targetWidth
                    << " | rectWidth=" << (rect ? rect->width() : -1)
                    << " | clipWidth=" << (clip.isValid() ? clip.width() : -1)
                    << "\n";
            }
        }
        qreal available = clip.isValid() && clip.width() > 0
                              ? clip.width()
                              : (rect ? rect->width() : -1);
        if (rect && rect->width() > 0 &&
            (available < 0 || rect->width() < available))
            available = rect->width();
        if (available > 0 && targetWidth > available + 1.0) {
            const qreal scale = available / qreal(targetWidth);
            if (scale < 0.5)
                return {}; // 实在太窄，保留英文
            g_graphFontScale = scale;
        }
        return target;
    }
    return target;
}

void hookPoint(QPainter *p, const QPoint &pos, const QString &text) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawPoint(p, pos, text); return; }
    const QString target = translateForPainter(p, text);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawPoint(p, pos, target.isEmpty() ? text : target);
    --g_paintDepth;
}

void hookPointF(QPainter *p, const QPointF &pos, const QString &text) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawPointF(p, pos, text); return; }
    const QString target = translateForPainter(p, text);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawPointF(p, pos, target.isEmpty() ? text : target);
    --g_paintDepth;
}

void hookPointF2(QPainter *p, const QPointF &pos, const QString &text, int a, int b) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawPointF2(p, pos, text, a, b); return; }
    const QString target = translateForPainter(p, text);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawPointF2(p, pos, target.isEmpty() ? text : target, a, b);
    --g_paintDepth;
}

void hookRect(QPainter *p, const QRect &rect, int flags, const QString &text, QRect *br) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawRect(p, rect, flags, text, br); return; }
    const QRectF rectF(rect);
    const QString target = translateForPainter(p, text, &rectF);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawRect(p, rect, flags, target.isEmpty() ? text : target, br);
    --g_paintDepth;
}

void hookRectFOption(QPainter *p, const QRectF &rect, const QString &text,
                     const QTextOption &option) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawRectFOption(p, rect, text, option); return; }
    const QString target = translateForPainter(p, text, &rect);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawRectFOption(p, rect, target.isEmpty() ? text : target, option);
    --g_paintDepth;
}

void hookRectFAlign(QPainter *p, const QRectF &rect, int flags, const QString &text,
                    QRectF *br) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawRectFAlign(p, rect, flags, text, br); return; }
    const QString target = translateForPainter(p, text, &rect);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawRectFAlign(p, rect, flags, target.isEmpty() ? text : target, br);
    --g_paintDepth;
}

void hookXY(QPainter *p, int x, int y, const QString &text) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawXY(p, x, y, text); return; }
    const QString target = translateForPainter(p, text);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawXY(p, x, y, target.isEmpty() ? text : target);
    --g_paintDepth;
}

void hookXYWH(QPainter *p, int x, int y, int w, int h, int flags,
              const QString &text, QRect *br) {
    CallScope scope;
    if (g_paintDepth > 0) { g_drawXYWH(p, x, y, w, h, flags, text, br); return; }
    const QRectF rectF(x, y, w, h);
    const QString target = translateForPainter(p, text, &rectF);
    ++g_paintDepth;
    PaintFontGuard fontGuard(p);
    g_drawXYWH(p, x, y, w, h, flags, target.isEmpty() ? text : target, br);
    --g_paintDepth;
}

bool replaceImportInModule(HMODULE module, void *original, void *replacement) {
    if (!module || !original || !replacement)
        return false;
    auto *base = reinterpret_cast<unsigned char *>(module);
    auto *dos = reinterpret_cast<IMAGE_DOS_HEADER *>(base);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
        return false;
    auto *nt = reinterpret_cast<IMAGE_NT_HEADERS *>(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
        return false;
    const DWORD importRva =
        nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (!importRva)
        return false;
    bool replaced = false;
    auto *descriptor = reinterpret_cast<IMAGE_IMPORT_DESCRIPTOR *>(base + importRva);
    for (; descriptor->Name; ++descriptor) {
        if (!descriptor->FirstThunk)
            continue;
        auto *thunk = reinterpret_cast<IMAGE_THUNK_DATA *>(base + descriptor->FirstThunk);
        for (; thunk->u1.Function; ++thunk) {
            auto **slot = reinterpret_cast<void **>(&thunk->u1.Function);
            if (*slot != original)
                continue;
            DWORD oldProtect = 0;
            if (!VirtualProtect(slot, sizeof(void *), PAGE_READWRITE, &oldProtect))
                continue;
            const bool changed =
                InterlockedCompareExchangePointer(slot, replacement, original) == original;
            DWORD ignored = 0;
            VirtualProtect(slot, sizeof(void *), oldProtect, &ignored);
            FlushInstructionCache(GetCurrentProcess(), slot, sizeof(void *));
            if (changed) {
                g_slots.push_back({slot, original, replacement});
                replaced = true;
            }
        }
    }
    return replaced;
}

bool replaceImportAllModules(void *original, void *replacement) {
    HMODULE modules[2048];
    DWORD needed = 0;
    if (!EnumProcessModules(GetCurrentProcess(), modules, sizeof(modules), &needed))
        return false;
    const DWORD count = qMin<DWORD>(needed / sizeof(HMODULE),
                                   sizeof(modules) / sizeof(HMODULE));
    bool any = false;
    for (DWORD i = 0; i < count; ++i) {
        HMODULE reference = nullptr;
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS,
                                reinterpret_cast<LPCWSTR>(modules[i]), &reference))
            continue;
        if (replaceImportInModule(modules[i], original, replacement)) {
            any = true;
            g_moduleRefs.push_back(reference);
        } else {
            FreeLibrary(reference);
        }
    }
    return any;
}

template <typename Function>
bool hookQtGuiSymbol(HMODULE qtGui, const char *symbol, Function hook,
                     Function *originalOut) {
    auto *original = reinterpret_cast<Function>(GetProcAddress(qtGui, symbol));
    if (!original)
        return false;
    *originalOut = original;
    return replaceImportAllModules(reinterpret_cast<void *>(original),
                                   reinterpret_cast<void *>(hook));
}

bool installHooks() {
    if (g_hooksInstalled)
        return !g_slots.empty();
    HMODULE qtGui = GetModuleHandleW(L"Qt6Gui.dll");
    if (!qtGui)
        return false;
    bool any = false;
    any |= hookQtGuiSymbol(qtGui, "?drawText@QPainter@@QEAAXAEBVQPoint@@AEBVQString@@@Z",
                           &hookPoint, &g_drawPoint);
    any |= hookQtGuiSymbol(qtGui, "?drawText@QPainter@@QEAAXAEBVQPointF@@AEBVQString@@@Z",
                           &hookPointF, &g_drawPointF);
    any |= hookQtGuiSymbol(qtGui,
                           "?drawText@QPainter@@QEAAXAEBVQPointF@@AEBVQString@@HH@Z",
                           &hookPointF2, &g_drawPointF2);
    any |= hookQtGuiSymbol(
        qtGui, "?drawText@QPainter@@QEAAXAEBVQRect@@HAEBVQString@@PEAV2@@Z",
        &hookRect, &g_drawRect);
    any |= hookQtGuiSymbol(
        qtGui,
        "?drawText@QPainter@@QEAAXAEBVQRectF@@AEBVQString@@AEBVQTextOption@@@Z",
        &hookRectFOption, &g_drawRectFOption);
    any |= hookQtGuiSymbol(
        qtGui, "?drawText@QPainter@@QEAAXAEBVQRectF@@HAEBVQString@@PEAV2@@Z",
        &hookRectFAlign, &g_drawRectFAlign);
    any |= hookQtGuiSymbol(qtGui, "?drawText@QPainter@@QEAAXHHAEBVQString@@@Z",
                           &hookXY, &g_drawXY);
    any |= hookQtGuiSymbol(
        qtGui, "?drawText@QPainter@@QEAAXHHHHHAEBVQString@@PEAVQRect@@@Z",
        &hookXYWH, &g_drawXYWH);
    g_hooksInstalled = true;
    return any;
}

void restoreHooks() {
    for (auto it = g_slots.rbegin(); it != g_slots.rend(); ++it) {
        if (!it->slot || *it->slot != it->replacement)
            continue;
        DWORD oldProtect = 0;
        if (!VirtualProtect(it->slot, sizeof(void *), PAGE_READWRITE, &oldProtect))
            continue;
        InterlockedCompareExchangePointer(it->slot, it->original, it->replacement);
        DWORD ignored = 0;
        VirtualProtect(it->slot, sizeof(void *), oldProtect, &ignored);
        FlushInstructionCache(GetCurrentProcess(), it->slot, sizeof(void *));
    }
    g_slots.clear();
    for (HMODULE module : g_moduleRefs)
        FreeLibrary(module);
    g_moduleRefs.clear();
    g_hooksInstalled = false;
}

void scanAllWidgets() {
    const auto widgets = QApplication::allWidgets();
    for (auto *widget : widgets) {
        scanWidgetTree(widget);
        observeSearchWidget(widget);
    }
}

} // namespace

XK_EXPORT int __cdecl xk_api_version() { return kApiVersion; }

XK_EXPORT const wchar_t *__cdecl xk_build_id() {
    return L"xingkong_zh_qt6 0.1.0";
}

XK_EXPORT void __cdecl xk_clear_translations() {
    g_exact.clear();
    g_normalized.clear();
    g_idTranslations.clear();
}

XK_EXPORT void __cdecl xk_add_id_translation(const wchar_t *id,
                                             const wchar_t *target) {
    if (!id || !target)
        return;
    const QString key = QString::fromWCharArray(id);
    const QString value = QString::fromWCharArray(target);
    if (!key.trimmed().isEmpty() && !value.isEmpty())
        g_idTranslations.insert(key, value);
}

XK_EXPORT void __cdecl xk_add_translation(const wchar_t *source,
                                          const wchar_t *target) {
    if (!source || !target)
        return;
    const QString src = QString::fromWCharArray(source);
    const QString dst = QString::fromWCharArray(target);
    if (src.trimmed().isEmpty() || dst.trimmed().isEmpty())
        return;
    g_exact.insert(src, dst);
    const QString norm = normalizeSource(src);
    if (!norm.isEmpty())
        g_normalized.insert(norm, dst);
    if (g_searchFilter)
        g_searchFilter->refresh();
}

XK_EXPORT int __cdecl xk_translation_count() { return g_exact.size(); }

XK_EXPORT int __cdecl xk_hook_count() { return static_cast<int>(g_slots.size()); }

XK_EXPORT int __cdecl xk_combo_count() { return static_cast<int>(g_comboBindings.size()); }

XK_EXPORT const char *__cdecl xk_combo_info() {
    static std::string info;
    info.clear();
    for (const auto &binding : g_comboBindings) {
        if (!binding.view)
            continue;
        info += binding.view->metaObject()->className();
        info += '|';
        info += binding.original
                    ? binding.original->metaObject()->className()
                    : "null";
        info += ';';
    }
    return info.c_str();
}

XK_EXPORT int __cdecl xk_view_count() {
    return static_cast<int>(g_viewBindings.size());
}

XK_EXPORT const char *__cdecl xk_view_info() {
    static std::string info;
    info.clear();
    for (const auto &binding : g_viewBindings) {
        if (!binding.view)
            continue;
        info += binding.view->metaObject()->className();
        info += '|';
        info += binding.view->model()
                    ? binding.view->model()->metaObject()->className()
                    : "null";
        info += '|';
        info += binding.original
                    ? binding.original->metaObject()->className()
                    : "null";
        info += ';';
    }
    return info.c_str();
}

XK_EXPORT void __cdecl xk_set_enabled(int enabled) {
    g_enabled = enabled != 0;
    if (g_searchFilter)
        g_searchFilter->setActive(g_enabled);
}

XK_EXPORT void __cdecl xk_set_fuzzy(int enabled) {
    g_fuzzy = enabled != 0;
}

XK_EXPORT void __cdecl xk_set_graph_enabled(int enabled) {
    g_graph = enabled != 0; // V1 预留，节点图翻译在 V2 实现
}

XK_EXPORT int __cdecl xk_install(void *applicationPointer) {
    auto *application = static_cast<QApplication *>(applicationPointer);
    if (!application)
        application = qobject_cast<QApplication *>(QCoreApplication::instance());
    if (!application || !onUiThread())
        return 0;
    installCrashFilter();
    if (!g_filter) {
        g_filter = new XingKongFilter(application);
        application->installEventFilter(g_filter);
    }
    if (!g_searchFilter)
        g_searchFilter = new ResourceSearchFilter(application);
    g_searchFilter->setActive(g_enabled);
    scanAllWidgets();
    installHooks();
    return 1;
}

XK_EXPORT int __cdecl xk_uninstall() {
    if (!onUiThread())
        return 0;
    g_enabled = false;
    if (g_activeCalls.load() != 0)
        return 0; // 还有绘制调用在栈上，等下一次卸载
    if (g_searchFilter) {
        g_searchFilter->shutdown();
        delete g_searchFilter;
        g_searchFilter = nullptr;
    }
    if (g_filter) {
        if (auto *app = qobject_cast<QApplication *>(QCoreApplication::instance()))
            app->removeEventFilter(g_filter);
        delete g_filter;
        g_filter = nullptr;
    }
    restoreDelegates();
    restoreComboDelegates();
    restoreCustomViewDelegates();
    restoreHooks();
    return 1;
}
