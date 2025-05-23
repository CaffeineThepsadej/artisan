#!/usr/bin/env python3
#

"""Check Combo Box
---------------
A QComboBox subclass designed for multiple item selection.
The combo box popup allows the user to check/uncheck multiple items at
once.
"""

# by Aleš Erjavec
# downloaded from https://gist.github.com/ales-erjavec/7624dd1d183dfbfb3354600b285abb94
# updatet to PyQt6, by Marko Luther 2021

import sys
from typing import Dict, Optional

try:
    from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import ( QStandardItemModel,  # @UnusedImport @Reimport  @UnresolvedImport
        QPalette, QFontMetrics, QBrush, QColor, QPixmap, QIcon # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt6.QtWidgets import (
        QComboBox, QAbstractItemDelegate, QStyledItemDelegate, # @UnusedImport @Reimport  @UnresolvedImport
        QApplication, QStyle, QStyleOptionComboBox, # @UnusedImport @Reimport  @UnresolvedImport
        QStyleOptionMenuItem, QStyleOptionViewItem, QStylePainter, QWidget # @UnusedImport @Reimport  @UnresolvedImport
    )
except ImportError:
    from PyQt5.QtCore import Qt, QEvent, QTimer, pyqtSignal # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import ( QStandardItemModel, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QPalette, QFontMetrics, QBrush, QColor, QPixmap, QIcon # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt5.QtWidgets import ( # type: ignore
        QComboBox, QAbstractItemDelegate, QStyledItemDelegate, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QApplication, QStyle, QStyleOptionComboBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QStyleOptionMenuItem, QStyleOptionViewItem, QStylePainter, QWidget # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    )


class CheckComboBox(QComboBox): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    """A QComboBox allowing multiple item selection.
    """

    flagChanged=pyqtSignal(int,bool)


    class ComboItemDelegate(QStyledItemDelegate): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
        """Helper styled delegate (mostly based on existing private Qt's
        delegate used by the QComboBox). Used to style the popup like a
        list view (e.g windows style).
        """
        def isSeparator(self, index): # pylint: disable=no-self-use
            return str(index.data(Qt.ItemDataRole.AccessibleDescriptionRole)) == 'separator'

        def paint(self, painter, option, index):
#            if option.widget is not None:
#                style = option.widget.style()
#            else:
#                style = QApplication.style()

            option = QStyleOptionViewItem(option)
            option.showDecorationSelected = True

            # option.state &= ~QStyle.StateFlag.State_HasFocus & ~QStyle.StateFlag.State_MouseOver
            if self.isSeparator(index):
                pass # the separator draws on the wrong height (always on first entry) in PyQt6
#                opt = QStyleOption()
#                opt.rect = QRect(option.rect)
#                if isinstance(option.widget, QAbstractItemView):
#                    opt.rect.setWidth(option.widget.viewport().width())
#                style.drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorToolBarSeparator,
#                                    opt, painter, option.widget)
            else:
                super().paint(painter, option, index)

    class ComboMenuDelegate(QAbstractItemDelegate): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
        """Helper styled delegate (mostly based on existing private Qt's
        delegate used by the QComboBox). Used to style the popup like a
        menu. (e.g osx aqua style).
        """

        __slots__ = [ '__popupIsShown', '__blockMouseReleaseTimer', '__initialMousePos', '__separator', '__placeholderText' ]

        def isSeparator(self, index): # pylint: disable=no-self-use
            return str(index.data(Qt.ItemDataRole.AccessibleDescriptionRole)) == 'separator'

        def paint(self, painter, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_MenuItem, menuopt, painter,
                              option.widget)

        def sizeHint(self, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = QApplication.style()
            return style.sizeFromContents(
                QStyle.ContentsType.CT_MenuItem, menuopt, menuopt.rect.size(),
                option.widget
            )

        def _getMenuStyleOption(self, option, index):
            menuoption = QStyleOptionMenuItem()
            palette = option.palette.resolve(QApplication.palette('QMenu'))
            foreground = index.data(Qt.ItemDataRole.ForegroundRole)
            if isinstance(foreground, (QBrush, QColor, QPixmap)):
                foreground = QBrush(foreground)
                palette.setBrush(QPalette.ColorRole.Text, foreground)
                palette.setBrush(QPalette.ColorRole.ButtonText, foreground)
                palette.setBrush(QPalette.ColorRole.WindowText, foreground)

            background = index.data(Qt.ItemDataRole.BackgroundRole)
            if isinstance(background, (QBrush, QColor, QPixmap)):
                background = QBrush(background)
                try:
                    palette.setBrush(QPalette.ColorRole.Base, background)
                except Exception:  # pylint: disable=broad-except
                    # old obsolete style:
                    palette.setBrush(QPalette.ColorRole.Background, background) # type: ignore


            menuoption.palette = palette

            decoration = index.data(Qt.ItemDataRole.DecorationRole)
            if isinstance(decoration, QIcon):
                menuoption.icon = decoration

            if self.isSeparator(index):
                menuoption.menuItemType = QStyleOptionMenuItem.MenuItemType.Separator
            else:
                menuoption.menuItemType = QStyleOptionMenuItem.MenuItemType.Normal

            if index.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                menuoption.checkType = QStyleOptionMenuItem.CheckType.NonExclusive
            else:
                menuoption.checkType = QStyleOptionMenuItem.CheckType.NotCheckable

            check = index.data(Qt.ItemDataRole.CheckStateRole)
            menuoption.checked = check == Qt.CheckState.Checked

            if option.widget is not None:
                menuoption.font = option.widget.font()
            else:
                menuoption.font = QApplication.font('QMenu')

            menuoption.maxIconWidth = option.decorationSize.width() + 4
            menuoption.rect = option.rect
            menuoption.menuRect = option.rect

            menuoption.menuHasCheckableItems = True
#            menuoption.tabWidth = 0
            # TODO: self.displayText(QVariant, QLocale) # pylint: disable=fixme
            # TODO: Why is this not a QStyledItemDelegate? # pylint: disable=fixme
            display = index.data(Qt.ItemDataRole.DisplayRole)
            if isinstance(display, str):
                menuoption.text = display
            else:
                menuoption.text = str(display)

            menuoption.fontMetrics = QFontMetrics(menuoption.font)
            state = option.state & (QStyle.StateFlag.State_MouseOver |
                                    QStyle.StateFlag.State_Selected |
                                    QStyle.StateFlag.State_Active)

            if index.flags() & Qt.ItemFlag.ItemIsEnabled:
                state = state | QStyle.StateFlag.State_Enabled
                menuoption.palette.setCurrentColorGroup(QPalette.ColorGroup.Active)
            else:
                state = state & ~QStyle.StateFlag.State_Enabled
                menuoption.palette.setCurrentColorGroup(QPalette.ColorGroup.Disabled)

            if menuoption.checked:
                state = state | QStyle.StateFlag.State_On
            else:
                state = state | QStyle.StateFlag.State_Off

            menuoption.state = state
            return menuoption

    def __init__(self, parent:Optional[QWidget] = None, placeholderText:str = '', separator:str = ', ',
                 **kwargs:Dict) -> None:
        super().__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.__popupIsShown = False
        self.__blockMouseReleaseTimer = QTimer(self)
        self.__blockMouseReleaseTimer.setSingleShot(True)
        self.__initialMousePos = None
        self.__separator = separator
        self.__placeholderText = placeholderText
        self.__updateItemDelegate()

    def mousePressEvent(self, event):
        """Reimplemented."""
        self.__popupIsShown = False
        super().mousePressEvent(event)
        if self.__popupIsShown:
            self.__initialMousePos = self.mapToGlobal(event.pos())
            self.__blockMouseReleaseTimer.start(
                QApplication.doubleClickInterval())

    def changeEvent(self, event):
        """Reimplemented."""
        if event.type() == QEvent.Type.StyleChange:
            self.__updateItemDelegate()
        super().changeEvent(event)

    def showPopup(self):
        """Reimplemented."""
        super().showPopup()
        view = self.view()
        if view is not None:
            view.installEventFilter(self)
            vp = view.viewport()
            if vp is not None:
                vp.installEventFilter(self)
                self.__popupIsShown = True

    def hidePopup(self):
        """Reimplemented."""
        view = self.view()
        if view is not None:
            view.removeEventFilter(self)
            vp = view.viewport()
            if vp is not None:
                vp.removeEventFilter(self)
            self.__popupIsShown = False
            self.__initialMousePos = None
            super().hidePopup()
            view.clearFocus()

    def eventFilter(self, obj, event):
        """Reimplemented."""
        view = self.view()
        if view is not None:
            if self.__popupIsShown and \
                    event.type() == QEvent.Type.MouseMove and \
                    view.isVisible() and self.__initialMousePos is not None:
                diff = obj.mapToGlobal(event.pos()) - self.__initialMousePos # type: ignore # mypy: Statement is unreachable
                if diff.manhattanLength() > 9 and \
                        self.__blockMouseReleaseTimer.isActive():
                    self.__blockMouseReleaseTimer.stop()
                # pass through

            if self.__popupIsShown and \
                    event.type() == QEvent.Type.MouseButtonRelease and \
                    view.isVisible() and \
                    view.rect().contains(event.pos()) and \
                    view.currentIndex().isValid() and \
                    view.currentIndex().flags() & Qt.ItemFlag.ItemIsSelectable and \
                    view.currentIndex().flags() & Qt.ItemFlag.ItemIsEnabled and \
                    view.currentIndex().flags() & Qt.ItemFlag.ItemIsUserCheckable and \
                    view.visualRect(view.currentIndex()).contains(event.pos()) and \
                    not self.__blockMouseReleaseTimer.isActive():
                index = view.currentIndex()
                model = self.model()
                if model is not None:
                    state = model.data(index, Qt.ItemDataRole.CheckStateRole)
                    model.setData(index,
                                  Qt.CheckState.Checked if state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked,
                                  Qt.ItemDataRole.CheckStateRole)
                    view.update(index)
                    self.update()
                    self.flagChanged.emit(index.row(),state == Qt.CheckState.Unchecked)
                    return True

            if self.__popupIsShown and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
                # toggle the current items check state
                index = view.currentIndex()
                model = self.model()
                if model is not None:
                    flags = model.flags(index)
                    state = model.data(index, Qt.ItemDataRole.CheckStateRole)
                    if flags & Qt.ItemFlag.ItemIsUserCheckable and \
                            flags & Qt.ItemFlag.ItemIsAutoTristate:
                        state = Qt.CheckState((int(state) + 1) % 3)
                    elif flags & Qt.ItemFlag.ItemIsUserCheckable:
                        state = Qt.CheckState.Checked if state != Qt.CheckState.Checked else Qt.CheckState.Unchecked
                    model.setData(index, state, Qt.ItemDataRole.CheckStateRole)
                    view.update(index)
                    self.update()
                    self.flagChanged.emit(index.row(),state != Qt.CheckState.Unchecked)
                    return True
                    # TODO: handle Qt.Key.Key_Enter, Key_Return? # pylint: disable=fixme

        return super().eventFilter(obj, event)

    def paintEvent(self, _event):
        """Reimplemented."""
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        # draw the icon and text
        checked = self.checkedIndices()
        if checked:
            items = [self.itemText(i) for i in checked]
            option.currentText = self.__separator.join(items)
        else:
            option.currentText = self.__placeholderText
            option.palette.setCurrentColorGroup(QPalette.ColorGroup.Disabled)

        option.currentIcon = QIcon()
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)

    def itemCheckState(self, index):
        """Return the check state for item at `index`
        Parameters
        ----------
        index : int
        Returns
        -------
        state : Qt.CheckState
        """
        state = self.itemData(index, role=Qt.ItemDataRole.CheckStateRole)
        if isinstance(state, (int, Qt.CheckState)):
            return Qt.CheckState(state)
        return Qt.CheckState.Unchecked

    def setItemCheckState(self, index, state):
        """Set the check state for item at `index` to `state`.
        Parameters
        ----------
        index : int
        state : Qt.CheckState
        """
        self.setItemData(index, state, Qt.ItemDataRole.CheckStateRole)

    def checkedIndices(self):
        """Return a list of indices of all checked items.
        Returns
        -------
        indices : List[int]
        """
        return [i for i in range(self.count())
                if self.itemCheckState(i) == Qt.CheckState.Checked]

    def setPlaceholderText(self, text):
        """Set the placeholder text.
        This text is displayed on the checkbox when there are no checked
        items.
        Parameters
        ----------
        text : str
        """
        if self.__placeholderText != text:
            self.__placeholderText = text
            self.update()

    def placeholderText(self):
        """Return the placeholder text.
        Returns
        -------
        text : str
        """
        return self.__placeholderText

    def wheelEvent(self, event): # pylint: disable=no-self-use
        """Reimplemented."""
        event.ignore()

    def keyPressEvent(self, event):
        """Reimplemented."""
        # Override the default QComboBox behavior
        if event.key() == Qt.Key.Key_Down and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.showPopup()
            return

        ignored = {Qt.Key.Key_Up, Qt.Key.Key_Down,
                   Qt.Key.Key_PageDown, Qt.Key.Key_PageUp,
                   Qt.Key.Key_Home, Qt.Key.Key_End}

        if event.key() in ignored:
            event.ignore()
            return

        super().keyPressEvent(event)

    def __updateItemDelegate(self):
        opt = QStyleOptionComboBox()
        opt.initFrom(self)
        style = self.style()
        if style is not None:
            if style.styleHint(QStyle.StyleHint.SH_ComboBox_Popup, opt, self):
                self.setItemDelegate(CheckComboBox.ComboMenuDelegate(self))
            else:
                self.setItemDelegate(CheckComboBox.ComboItemDelegate(self))

def example():
    app = QApplication(list(sys.argv))
    cb = CheckComboBox(placeholderText='None')
    model = cb.model()
    if model is not None:
        assert isinstance(model, QStandardItemModel)
        cb.addItem('First')
        item0 = model.item(0)
        if item0 is not None:
            item0.setCheckable(True)
        cb.addItem('Second')
        item1 = model.item(1)
        if item1 is not None:
            item1.setCheckable(True)
        cb.addItem('Third')
        item2 = model.item(2)
        if item2 is not None:
            item2.setCheckable(True)
        cb.insertSeparator(3)
        cb.addItem('Fourth - Disabled')
        item4 = model.item(4)
        if item4 is not None:
            item4.setEnabled(False)
        cb.show()
        cb.raise_()

    return app.exec()

if __name__ == '__main__':
    sys.exit(example())
