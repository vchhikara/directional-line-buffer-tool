"""Small native Qt dialog for buffer parameters."""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QVBoxLayout,
)


def tr(message):
    return QCoreApplication.translate('DirectionalLineBuffer', message)


class BufferDialog(QDialog):
    def __init__(self, parent=None, destination_text=''):
        super().__init__(parent)
        self.setWindowTitle(tr('Directional Line Buffer'))
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        hint = QLabel(tr('Enter a distance and choose the buffer side relative to digitizing direction.'))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        self.distance = QDoubleSpinBox(self)
        self.distance.setRange(0.01, 100000000.0)
        self.distance.setDecimals(3)
        self.distance.setValue(10.0)
        self.distance.setSuffix(tr(' m'))
        self.distance.setToolTip(tr('Buffer distance in meters, measured in the project CRS'))
        form.addRow(tr('Distance:'), self.distance)

        self.side_combo = QComboBox(self)
        self.side_combo.addItem(tr('Both sides'), 'both')
        self.side_combo.addItem(tr('Left side'), 'left')
        self.side_combo.addItem(tr('Right side'), 'right')
        form.addRow(tr('Buffer side:'), self.side_combo)
        layout.addLayout(form)

        if destination_text:
            destination_label = QLabel(destination_text)
            destination_label.setWordWrap(True)
            layout.addWidget(destination_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def distance_meters(self):
        return self.distance.value()

    def side(self):
        return self.side_combo.currentData()
