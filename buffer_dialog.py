from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QDialogButtonBox, QLabel


class BufferDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Directional Line Buffer')
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Enter the buffer distance and choose the side relative to the digitizing direction.'))

        form = QFormLayout()
        self.distance = QDoubleSpinBox()
        self.distance.setRange(0.01, 100000000.0)
        self.distance.setDecimals(3)
        self.distance.setValue(10.0)
        self.distance.setSuffix(' m')
        self.distance.setToolTip('Buffer distance in meters')
        form.addRow('Distance:', self.distance)

        self.side_combo = QComboBox()
        self.side_combo.addItem('Both sides', 'both')
        self.side_combo.addItem('Left side', 'left')
        self.side_combo.addItem('Right side', 'right')
        form.addRow('Buffer side:', self.side_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def distance_meters(self):
        return self.distance.value()

    def side(self):
        return self.side_combo.currentData()

