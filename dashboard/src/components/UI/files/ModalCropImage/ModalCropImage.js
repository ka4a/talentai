import React, { useCallback, useState, useEffect, useRef, memo } from 'react';
import ImageCrop from 'react-image-crop';

import 'react-image-crop/dist/ReactCrop.css';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';

import Modal from '@components/UI/Modal';
import { withNewExtension, showErrorToast } from '@utils';
import FormSection from '@components/UI/FormSection';
import FormSubsection from '@components/UI/FormSection/FormSubsection';
import { Typography } from '@components';

import styles from './ModalCropImage.module.scss';

function ModalCropImage(props) {
  const { onSave, onClose, isOpen, file } = props;

  const [crop, setCrop] = useState(INITIAL_CROP);

  const [completedCrop, setCompletedCrop] = useState(null);

  const fileSrc = useLoadedFileSrc(file);
  const fileName = file?.name;

  const imageRef = useRef(null);
  const handleImageLoad = useCallback((image) => {
    imageRef.current = image;

    setCrop((crop) => ({ ...crop, ...fitAndCenterCrop(image, crop.aspect) }));
    // must be false if we change crop state
    return false;
  }, []);

  const handleClose = useCallback(() => {
    setCrop(INITIAL_CROP);
    onClose();
  }, [onClose]);

  const previewCanvasRef = useRef(null);

  const handleSave = useCallback(async () => {
    if (!onSave) return;
    try {
      const canvas = previewCanvasRef.current;

      const blob = await canvasToBlob(canvas, completedCrop);
      onSave(new File([blob], withNewExtension(fileName, 'png')));
    } catch (error) {
      showErrorToast(error.message);
    }
  }, [onSave, fileName, completedCrop]);

  useEffect(() => {
    const canvas = previewCanvasRef.current;
    const image = imageRef.current;

    if (completedCrop && canvas && image) {
      drawPreview(canvas, image, completedCrop);
    }
  }, [completedCrop]);

  return (
    <Modal
      size='huge'
      title={t`Crop Image`}
      isOpen={isOpen}
      isSaveDisabled={!completedCrop}
      onSave={handleSave}
      onClose={handleClose}
      onCancel={noop}
    >
      <div>
        <FormSection>
          <FormSubsection isGrid columnCount={3}>
            <Typography className={styles.description}>
              <Trans>
                Click and drag on unselected area to select area you want cropped. Drag
                selection in the middle to move it. Drag corners of the selection to
                resize it. Click outside the selection to deselect
              </Trans>
            </Typography>
            <ImageCrop
              className={styles.crop}
              circularCrop
              crop={crop}
              imageStyle={IMAGE_STYLE}
              onImageLoaded={handleImageLoad}
              onChange={setCrop}
              onComplete={setCompletedCrop}
              src={fileSrc}
            />
            <canvas ref={previewCanvasRef} className={styles.preview} />
          </FormSubsection>
        </FormSection>
      </div>
    </Modal>
  );
}

ModalCropImage.propTypes = {
  file: PropTypes.instanceOf(File),
  isOpen: PropTypes.bool,
  onSave: PropTypes.func,
  onClose: PropTypes.func,
};

const IMAGE_STYLE = {
  maxWidth: '100%',
  maxHeight: '400px',
};

const INITIAL_CROP = {
  aspect: 1,
  minHeight: 20,
  minWidth: 20,
};

function noop() {}

function useLoadedFileSrc(file) {
  const [url, setUrl] = useState('');

  useEffect(() => {
    if (!file) return;
    const newUrl = URL.createObjectURL(file);
    setUrl(newUrl);
    return () => {
      URL.revokeObjectURL(newUrl);
    };
  }, [file]);

  return url;
}

const canvasToBlob = (canvas, crop) =>
  new Promise((resolve, reject) => {
    if (!canvas) return reject(new Error(t`Failed to crop the image`));
    if (!crop) return reject(new Error(t`Cropped area isn't specified`));
    canvas.toBlob((blob) => resolve(blob), 'image/png', 1);
  });

function drawPreview(canvas, image, crop) {
  const scaleX = image.naturalWidth / image.width;
  const scaleY = image.naturalHeight / image.height;
  const drawingContext = canvas.getContext('2d');
  const pixelRatio = window.devicePixelRatio;

  canvas.width = crop.width * pixelRatio * scaleX;
  canvas.height = crop.height * pixelRatio * scaleY;

  // Scaling canvas
  drawingContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  drawingContext.imageSmoothingQuality = 'high';

  drawingContext.drawImage(
    image,
    // Specifying rectangle we cut from the image
    crop.x * scaleX,
    crop.y * scaleY,
    crop.width * scaleX,
    crop.height * scaleY,
    // Specifying where they would be drawn on the canvas
    0,
    0,
    crop.width * scaleX,
    crop.height * scaleY
  );
}

function fitAndCenterCrop(image, aspect) {
  let width = image.width;
  let height = width * aspect;

  if (height > image.height) {
    height = image.height;
    width = height / aspect;
    // It only completes the crop, if you have height, or width;
    return { height, x: (image.width - width) * 0.5 };
  }

  return { width, y: (image.height - height) * 0.5 };
}

export default memo(ModalCropImage);
