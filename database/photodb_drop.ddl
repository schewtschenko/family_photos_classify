ALTER TABLE image DROP CONSTRAINT image_camera_id_fkey;
ALTER TABLE image_location DROP CONSTRAINT image_location_image_id_fkey;
ALTER TABLE image_location DROP CONSTRAINT image_location_location_id_fkey;
ALTER TABLE image DROP CONSTRAINT image_subfolder_id_fkey;
ALTER TABLE location DROP CONSTRAINT location_city_id;
ALTER TABLE location DROP CONSTRAINT location_country_id_fkey;
ALTER TABLE location DROP CONSTRAINT location_region_id_fkey;
DROP TABLE IF EXISTS camera CASCADE;
DROP TABLE IF EXISTS city CASCADE;
DROP TABLE IF EXISTS country CASCADE;
DROP TABLE IF EXISTS image CASCADE;
DROP TABLE IF EXISTS image_location CASCADE;
DROP TABLE IF EXISTS location CASCADE;
DROP TABLE IF EXISTS region CASCADE;
DROP TABLE IF EXISTS subfolder CASCADE;
